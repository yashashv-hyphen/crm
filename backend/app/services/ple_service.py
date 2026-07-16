import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from app.models.ple_record import PleRecord
from app.models.ple_record_history import PleRecordHistory
from app.models.lead import Lead
from app.models.user import User
from app.schemas.ple import (
    PleAgentSummaryRow, PleMcidDetailRow, PleMcidUpdateRequest, PleRecordHistoryEntry,
)

MAX_MCID_ROWS = 5000


async def get_agent_summary(db: AsyncSession) -> list[PleAgentSummaryRow]:
    agent_label = func.coalesce(User.full_name, PleRecord.agent_name, "Unassigned")
    result = await db.execute(
        select(
            agent_label.label("agent"),
            PleRecord.agent_user_id.label("agent_user_id"),
            func.count(PleRecord.id).label("num_launches"),
            func.sum(case((PleRecord.fba_status.isnot(None), 1), else_=0)).label("fba_status_count"),
            func.coalesce(func.sum(PleRecord.fba_live_selection), 0).label("fba_live_selection"),
            func.sum(case((PleRecord.sp_status.isnot(None), 1), else_=0)).label("sp_status_count"),
            func.sum(case((PleRecord.cp_adoption.isnot(None), 1), else_=0)).label("cp_adoption_count"),
            func.sum(case((PleRecord.narf_cross_launch.isnot(None), 1), else_=0)).label("narf_cross_launch_count"),
            func.coalesce(func.sum(PleRecord.buyable_asin), 0).label("buyable_asin"),
        )
        .select_from(PleRecord)
        .outerjoin(User, User.id == PleRecord.agent_user_id)
        .group_by(agent_label, PleRecord.agent_user_id)
        .order_by(func.count(PleRecord.id).desc())
    )
    return [PleAgentSummaryRow(**row._mapping) for row in result.all()]


def _to_mcid_detail_row(rec: PleRecord, call_count: int | None, total_call_time) -> PleMcidDetailRow:
    row = PleMcidDetailRow.model_validate(rec)
    row.call_count = call_count
    row.total_call_time = float(total_call_time) if total_call_time is not None else None
    return row


async def get_mcid_detail(db: AsyncSession, agent_user_id: uuid.UUID | None = None) -> list[PleMcidDetailRow]:
    query = (
        select(PleRecord, Lead.call_count, Lead.total_call_time)
        .outerjoin(Lead, Lead.merchant_id == PleRecord.mcid)
        .order_by(PleRecord.mcid)
        .limit(MAX_MCID_ROWS)
    )
    if agent_user_id is not None:
        query = query.where(PleRecord.agent_user_id == agent_user_id)
    result = await db.execute(query)
    return [_to_mcid_detail_row(rec, call_count, total_call_time) for rec, call_count, total_call_time in result.all()]


_EDITABLE_FIELDS = {
    "fba_status", "sp_status", "cl_status", "cp_adoption", "narf_cross_launch",
    "launch_yn", "sp_yn", "coupons_yn", "cross_launch_final_stage",
    "launch_date", "fba_launch_date", "sp_launch_date", "cp_launch_date",
}


async def get_mcid_record(db: AsyncSession, mcid: str, current_user: User) -> PleRecord:
    result = await db.execute(select(PleRecord).where(PleRecord.mcid == mcid))
    rec = result.scalar_one_or_none()
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCID not found")
    if current_user.role == "fos" and rec.agent_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your MCID")
    return rec


async def update_mcid_record(
    db: AsyncSession, mcid: str, updates: PleMcidUpdateRequest, current_user: User,
) -> PleMcidDetailRow:
    rec = await get_mcid_record(db, mcid, current_user)

    update_data = updates.model_dump(exclude_unset=True)
    for field, new_value in update_data.items():
        assert field in _EDITABLE_FIELDS, f"{field} is not editable"
        old_value = getattr(rec, field, None)
        if old_value != new_value:
            db.add(PleRecordHistory(
                id=uuid.uuid4(),
                ple_record_id=rec.id,
                field_name=field,
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(new_value) if new_value is not None else None,
                performed_by=current_user.id,
            ))
            setattr(rec, field, new_value)

    if rec.launch_date and rec.launch_week:
        rec.launch_yn = "Yes"

    rec.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(rec)

    lead_row = (await db.execute(
        select(Lead.call_count, Lead.total_call_time).where(Lead.merchant_id == rec.mcid)
    )).first()
    call_count, total_call_time = lead_row if lead_row else (None, None)
    return _to_mcid_detail_row(rec, call_count, total_call_time)


async def get_mcid_history(db: AsyncSession, mcid: str, current_user: User) -> list[PleRecordHistoryEntry]:
    rec = await get_mcid_record(db, mcid, current_user)
    result = await db.execute(
        select(PleRecordHistory, User.full_name)
        .join(User, User.id == PleRecordHistory.performed_by)
        .where(PleRecordHistory.ple_record_id == rec.id)
        .order_by(PleRecordHistory.performed_at.asc())
    )
    return [
        PleRecordHistoryEntry(
            field_name=h.field_name,
            old_value=h.old_value,
            new_value=h.new_value,
            performed_by_name=name,
            performed_at=h.performed_at,
        )
        for h, name in result.all()
    ]
