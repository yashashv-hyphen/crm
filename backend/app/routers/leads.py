import uuid
import io
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.models.lead import Lead
from app.models.lead_history import LeadHistory
from app.schemas.lead import (
    LeadResponse, LeadUpdateRequest, LeadFilters,
    BulkUpdateRequest, PaginatedLeads, LeadHistoryEntry,
    NewRegistrationRequest,
)
from app.services import lead_service

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("/follow-ups", response_model=list[LeadResponse])
async def get_follow_ups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Lead).where(Lead.follow_up_date.isnot(None), Lead.is_archived == False)  # noqa: E712
    if current_user.role == "fos":
        query = query.where(Lead.assigned_fos_id == current_user.id)
    query = query.order_by(Lead.follow_up_date.asc())
    result = await db.execute(query)
    leads = result.scalars().all()
    return [await lead_service.enrich_lead(lead, db) for lead in leads]


@router.get("/search", response_model=list[LeadResponse])
async def search_leads(
    q: str = Query(..., description="Comma-separated Merchant IDs or mobile numbers"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    terms = [t.strip() for t in q.split(",") if t.strip()]
    if not terms:
        return []
    query = select(Lead).where(
        or_(
            Lead.merchant_id.in_(terms),
            Lead.mobile_number.in_(terms),
        )
    )
    if current_user.role == "fos":
        query = query.where(Lead.assigned_fos_id == current_user.id)
    result = await db.execute(query)
    leads = result.scalars().all()
    return [await lead_service.enrich_lead(lead, db) for lead in leads]


@router.get("/download")
async def download_leads(
    activity_id: uuid.UUID | None = None,
    fos_id: uuid.UUID | None = None,
    current_stage: str | None = None,
    sub_disposition: str | None = None,
    week_no: int | None = None,
    year: int | None = None,
    is_archived: bool = False,
    from_date: date | None = None,
    to_date: date | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = LeadFilters(
        activity_id=activity_id,
        fos_id=fos_id if current_user.role == "admin" else None,
        current_stage=current_stage,
        sub_disposition=sub_disposition,
        week_no=week_no,
        year=year,
        is_archived=is_archived,
        from_date=from_date,
        to_date=to_date,
    )
    result = await lead_service.get_leads(filters, page=1, size=10000, user=current_user, db=db)
    # Re-fetch raw leads for Excel export (we need Lead models not enriched responses)
    from app.services.lead_service import _build_lead_query
    query = _build_lead_query(filters, current_user)
    raw_result = await db.execute(query)
    leads = raw_result.scalars().all()
    excel_bytes = lead_service.leads_to_excel(leads)

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=leads.xlsx"},
    )


@router.get("", response_model=PaginatedLeads)
async def list_leads(
    activity_id: uuid.UUID | None = None,
    fos_id: uuid.UUID | None = None,
    current_stage: str | None = None,
    assigned_stage_bucket: str | None = None,
    current_stage_bucket: str | None = None,
    sub_disposition: str | None = None,
    follow_up_date: date | None = None,
    aging_color: str | None = None,
    week_no: int | None = None,
    year: int | None = None,
    is_archived: bool = False,
    from_date: date | None = None,
    to_date: date | None = None,
    upload_file_id: uuid.UUID | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = LeadFilters(
        activity_id=activity_id,
        fos_id=fos_id if current_user.role == "admin" else None,
        current_stage=current_stage,
        assigned_stage_bucket=assigned_stage_bucket,
        current_stage_bucket=current_stage_bucket,
        sub_disposition=sub_disposition,
        follow_up_date=follow_up_date,
        aging_color=aging_color,
        week_no=week_no,
        year=year,
        is_archived=is_archived,
        from_date=from_date,
        to_date=to_date,
        upload_file_id=upload_file_id,
    )
    return await lead_service.get_leads(filters, page=page, size=size, user=current_user, db=db)


@router.get("/{lead_id}/history", response_model=list[LeadHistoryEntry])
async def get_lead_history(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if current_user.role == "fos" and lead.assigned_fos_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    history_result = await db.execute(
        select(LeadHistory, User.full_name)
        .join(User, LeadHistory.performed_by == User.id)
        .where(LeadHistory.lead_id == lead_id)
        .order_by(LeadHistory.performed_at.asc())
    )
    rows = history_result.all()
    return [
        LeadHistoryEntry(
            action_type=h.action_type,
            old_value=h.old_value,
            new_value=h.new_value,
            performed_by_name=name,
            performed_at=h.performed_at,
        )
        for h, name in rows
    ]


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if current_user.role == "fos" and lead.assigned_fos_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return await lead_service.enrich_lead(lead, db)


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: uuid.UUID,
    body: LeadUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await lead_service.update_lead(lead_id, body, current_user, db)


@router.post("/register", response_model=LeadResponse, status_code=201)
async def create_new_registration(
    body: NewRegistrationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import datetime, timezone, date as date_type
    from app.services.lead_service import enrich_lead

    merchant_id = f"NR-{str(uuid.uuid4())[:8].upper()}"
    today = date_type.today()

    lead = Lead(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        mobile_number=body.mobile_number.strip(),
        email_id=body.email_id.strip() if body.email_id else None,
        seller_name=body.seller_name.strip() if body.seller_name else None,
        stage_assigned="New Registration",
        current_stage="New Registration",
        date_of_assignment=today,
        assigned_fos_id=current_user.id,
        is_self_created=True,
    )
    db.add(lead)
    await db.flush()
    result = await enrich_lead(lead, db)
    await db.commit()
    return result


@router.post("/bulk-update")
async def bulk_update(
    body: BulkUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await lead_service.bulk_update_leads(body, current_user, db)
