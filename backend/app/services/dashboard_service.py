import uuid
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.lead import Lead
from app.models.activity import Activity
from app.models.user import User
from app.schemas.dashboard import (
    FOSDashboardResponse, AdminDashboardResponse,
    StageSummaryRow, DispositionSummaryRow, AgentStageSummary,
)


async def _stage_summary_for_fos(fos_id: uuid.UUID, db: AsyncSession, from_date=None, to_date=None, year=None) -> list[StageSummaryRow]:
    result = await db.execute(
        select(Activity).where(Activity.is_active == True).order_by(Activity.position_order)  # noqa: E712
    )
    activities = result.scalars().all()
    rows = []
    for act in activities:
        base = select(func.count()).where(
            Lead.current_activity_id == act.id,
            Lead.assigned_fos_id == fos_id,
            Lead.is_archived == False,  # noqa: E712
        )
        if year:
            base = base.where(Lead.year == year)
        if from_date:
            base = base.where(Lead.date_of_assignment >= from_date)
        if to_date:
            base = base.where(Lead.date_of_assignment <= to_date)

        total_result = await db.execute(base)
        total = total_result.scalar() or 0

        moved_result = await db.execute(
            base.where(Lead.final_stage.isnot(None))
        )
        moved = moved_result.scalar() or 0

        if total > 0 or moved > 0:
            rows.append(StageSummaryRow(
                activity_id=act.id,
                activity_name=act.name,
                total_assigned=total,
                moved_to_next=moved,
                pending=total - moved,
            ))
    return rows


async def _disposition_summary(fos_id: uuid.UUID | None, db: AsyncSession) -> list[DispositionSummaryRow]:
    from datetime import datetime, timedelta
    from sqlalchemy import extract
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    base_cond = [Lead.sub_disposition.isnot(None), Lead.is_archived == False]  # noqa: E712
    if fos_id:
        base_cond.append(Lead.assigned_fos_id == fos_id)

    ytd_result = await db.execute(
        select(Lead.sub_disposition, func.count().label("cnt"))
        .where(*base_cond)
        .group_by(Lead.sub_disposition)
    )
    ytd_map = {r.sub_disposition: r.cnt for r in ytd_result}

    week_cond = base_cond + [Lead.updated_at >= week_start]
    week_result = await db.execute(
        select(Lead.sub_disposition, func.count().label("cnt"))
        .where(*week_cond)
        .group_by(Lead.sub_disposition)
    )
    week_map = {r.sub_disposition: r.cnt for r in week_result}

    rows = []
    for sd, ytd_count in ytd_map.items():
        rows.append(DispositionSummaryRow(
            sub_disposition=sd,
            this_week=week_map.get(sd, 0),
            ytd=ytd_count,
        ))
    return sorted(rows, key=lambda r: r.ytd, reverse=True)


async def get_fos_dashboard(fos_id: uuid.UUID, db: AsyncSession) -> FOSDashboardResponse:
    stage_summary = await _stage_summary_for_fos(fos_id, db)
    disposition_summary = await _disposition_summary(fos_id, db)

    today = date.today()
    fu_result = await db.execute(
        select(func.count()).where(
            Lead.assigned_fos_id == fos_id,
            Lead.follow_up_date == today,
            Lead.is_archived == False,  # noqa: E712
        )
    )
    follow_up_today_count = fu_result.scalar() or 0

    return FOSDashboardResponse(
        stage_summary=stage_summary,
        disposition_summary=disposition_summary,
        follow_up_today_count=follow_up_today_count,
    )


async def get_admin_dashboard(
    year: int | None,
    from_date,
    to_date,
    fos_id: uuid.UUID | None,
    activity_id: uuid.UUID | None,
    db: AsyncSession,
) -> AdminDashboardResponse:
    # Overall summary
    result = await db.execute(
        select(Activity).where(Activity.is_active == True).order_by(Activity.position_order)  # noqa: E712
    )
    activities = result.scalars().all()

    overall: list[StageSummaryRow] = []
    for act in activities:
        if activity_id and act.id != activity_id:
            continue
        base = select(func.count()).where(
            Lead.current_activity_id == act.id,
            Lead.is_archived == False,  # noqa: E712
        )
        if year:
            base = base.where(Lead.year == year)
        if from_date:
            base = base.where(Lead.date_of_assignment >= from_date)
        if to_date:
            base = base.where(Lead.date_of_assignment <= to_date)
        if fos_id:
            base = base.where(Lead.assigned_fos_id == fos_id)

        total = (await db.execute(base)).scalar() or 0
        moved = (await db.execute(base.where(Lead.final_stage.isnot(None)))).scalar() or 0

        overall.append(StageSummaryRow(
            activity_id=act.id,
            activity_name=act.name,
            total_assigned=total,
            moved_to_next=moved,
            pending=total - moved,
        ))

    # Agent-wise summary
    fos_result = await db.execute(
        select(User).where(User.role == "fos", User.is_active == True)  # noqa: E712
    )
    all_fos = fos_result.scalars().all()
    if fos_id:
        all_fos = [u for u in all_fos if u.id == fos_id]

    agent_summaries: list[AgentStageSummary] = []
    for fos_user in all_fos:
        summary = await _stage_summary_for_fos(fos_user.id, db, from_date, to_date, year)
        if summary:
            agent_summaries.append(AgentStageSummary(
                fos_id=fos_user.id,
                fos_name=fos_user.full_name,
                stage_summary=summary,
            ))

    disposition_summary = await _disposition_summary(fos_id, db)

    return AdminDashboardResponse(
        overall_stage_summary=overall,
        agent_wise_summary=agent_summaries,
        disposition_summary=disposition_summary,
    )
