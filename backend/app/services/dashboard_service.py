import uuid
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.lead import Lead
from app.models.activity import Activity
from app.models.user import User
from app.services.movement_engine import _activity_entry_field
from app.services.stage_bucketing import (
    STAGE_BUCKETS, ROW_STAGE_BUCKETS, bucket_assigned_stage, bucket_current_stage,
)
from app.schemas.dashboard import (
    FOSDashboardResponse, AdminDashboardResponse,
    StageSummaryRow, StageMatrixRow, StageMatrixResponse,
    DispositionSummaryRow, AgentStageSummary,
)

# Activities inside the RNC/IDV/RTL flow are covered by the Stage Summary
# matrix (see _build_stage_matrix) instead of a per-activity row.
_FLOW_ENTRY_FIELDS = {"rnc_entry_date", "idv_entry_date", "rtl_entry_date"}


def _apply_common_filters(query, fos_id, year, from_date, to_date):
    if fos_id:
        query = query.where(Lead.assigned_fos_id == fos_id)
    if year:
        query = query.where(Lead.year == year)
    if from_date:
        query = query.where(Lead.date_of_assignment >= from_date)
    if to_date:
        query = query.where(Lead.date_of_assignment <= to_date)
    return query


async def _legacy_stage_row(
    act: Activity, fos_id: uuid.UUID | None, db: AsyncSession,
    from_date=None, to_date=None, year=None,
) -> StageSummaryRow:
    """Row for stages outside the RNC/IDV/RTL flow (FBA/SP/Open Spending/NARF/GSI) —
    unchanged from the original current-activity-based logic."""
    base = select(func.count()).where(
        Lead.current_activity_id == act.id,
        Lead.is_archived == False,  # noqa: E712
    )
    base = _apply_common_filters(base, fos_id, year, from_date, to_date)

    total = (await db.execute(base)).scalar() or 0
    moved = (await db.execute(base.where(Lead.final_stage.isnot(None)))).scalar() or 0

    return StageSummaryRow(
        activity_id=act.id,
        activity_name=act.name,
        total_assigned=total,
        pending=total - moved,
    )


async def _build_activity_rows(
    activities: list[Activity], fos_id: uuid.UUID | None, db: AsyncSession,
    from_date=None, to_date=None, year=None, activity_id_filter: uuid.UUID | None = None,
) -> list[StageSummaryRow]:
    """Builds stage rows for activities outside the RNC/IDV/RTL flow — those
    are covered by the Stage Summary matrix instead (see _build_stage_matrix)."""
    rows: list[StageSummaryRow] = []
    for act in activities:
        if activity_id_filter and act.id != activity_id_filter:
            continue

        entry_field = _activity_entry_field(act.name)
        if entry_field in _FLOW_ENTRY_FIELDS:
            continue

        row = await _legacy_stage_row(act, fos_id, db, from_date, to_date, year)
        # GSI always renders (alongside New Registration) regardless of count;
        # the other legacy stages only render when they have data.
        if entry_field == "gsi_entry_date" or row.total_assigned > 0:
            rows.append(row)

    return rows


async def _build_stage_matrix(
    fos_id: uuid.UUID | None, db: AsyncSession, from_date=None, to_date=None, year=None,
) -> StageMatrixResponse:
    """Cross-tabs leads by (originally assigned stage, currently at stage) across
    the RNC/IDV/RTL/Launch flow, with an Other bucket for anything outside it."""
    query = select(Lead.stage_assigned, Lead.current_stage, Lead.final_stage).where(
        Lead.is_archived == False,  # noqa: E712
    )
    query = _apply_common_filters(query, fos_id, year, from_date, to_date)
    result = (await db.execute(query)).all()

    counts = {a: {c: 0 for c in STAGE_BUCKETS} for a in ROW_STAGE_BUCKETS}
    for stage_assigned, current_stage, final_stage in result:
        assigned_bucket = bucket_assigned_stage(stage_assigned)
        current_bucket = bucket_current_stage(current_stage, final_stage)
        counts[assigned_bucket][current_bucket] += 1

    return StageMatrixResponse(
        stages=STAGE_BUCKETS,
        rows=[StageMatrixRow(assigned_stage=a, cells=counts[a]) for a in ROW_STAGE_BUCKETS],
    )


async def _stage_summary_for_fos(fos_id: uuid.UUID, db: AsyncSession, from_date=None, to_date=None, year=None) -> list[StageSummaryRow]:
    result = await db.execute(
        select(Activity).where(Activity.is_active == True).order_by(Activity.position_order)  # noqa: E712
    )
    activities = result.scalars().all()
    rows = await _build_activity_rows(activities, fos_id, db, from_date, to_date, year)

    nr_total = (await db.execute(
        select(func.count()).where(
            Lead.assigned_fos_id == fos_id,
            Lead.is_self_created == True,  # noqa: E712
            Lead.is_archived == False,  # noqa: E712
        )
    )).scalar() or 0
    if nr_total > 0:
        rows.append(StageSummaryRow(
            activity_id=None,
            activity_name="New Registration",
            total_assigned=nr_total,
            pending=nr_total,
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
    stage_matrix = await _build_stage_matrix(fos_id, db)
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
        stage_matrix=stage_matrix,
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

    overall = await _build_activity_rows(
        activities, fos_id, db, from_date, to_date, year, activity_id_filter=activity_id,
    )

    # A single-activity filter doesn't make sense for a full cross-tab matrix,
    # so only compute it for the unfiltered overall view.
    if activity_id:
        overall_stage_matrix = StageMatrixResponse(
            stages=STAGE_BUCKETS,
            rows=[StageMatrixRow(assigned_stage=a, cells={c: 0 for c in STAGE_BUCKETS}) for a in ROW_STAGE_BUCKETS],
        )
    else:
        overall_stage_matrix = await _build_stage_matrix(fos_id, db, from_date, to_date, year)

    # New Registration row for overall summary (only when no activity_id filter)
    if not activity_id:
        nr_base = select(func.count()).where(
            Lead.is_self_created == True,  # noqa: E712
            Lead.is_archived == False,  # noqa: E712
        )
        if fos_id:
            nr_base = nr_base.where(Lead.assigned_fos_id == fos_id)
        nr_total = (await db.execute(nr_base)).scalar() or 0
        if nr_total > 0:
            overall.append(StageSummaryRow(
                activity_id=None,
                activity_name="New Registration",
                total_assigned=nr_total,
                pending=nr_total,
            ))

    # Agent-wise summary — derive FOS list from leads so inactive/deleted users still appear
    fos_ids_result = await db.execute(
        select(Lead.assigned_fos_id).where(
            Lead.is_archived == False,  # noqa: E712
            Lead.assigned_fos_id.isnot(None),
        ).distinct()
    )
    all_fos_ids = [r[0] for r in fos_ids_result.fetchall()]
    if fos_id:
        all_fos_ids = [f for f in all_fos_ids if f == fos_id]

    # Build id→name map from users table (any role/status)
    if all_fos_ids:
        users_result = await db.execute(
            select(User.id, User.full_name).where(User.id.in_(all_fos_ids))
        )
        fos_name_map = {r.id: r.full_name for r in users_result.fetchall()}
    else:
        fos_name_map = {}

    agent_summaries: list[AgentStageSummary] = []
    for fid in all_fos_ids:
        summary = await _stage_summary_for_fos(fid, db, from_date, to_date, year)
        if summary:
            agent_summaries.append(AgentStageSummary(
                fos_id=fid,
                fos_name=fos_name_map.get(fid, f"Unknown ({str(fid)[:8]})"),
                stage_summary=summary,
            ))

    disposition_summary = await _disposition_summary(fos_id, db)

    total_leads_result = await db.execute(
        select(func.count()).where(Lead.is_archived == False)  # noqa: E712
    )
    total_leads = total_leads_result.scalar() or 0

    return AdminDashboardResponse(
        total_leads=total_leads,
        overall_stage_summary=overall,
        overall_stage_matrix=overall_stage_matrix,
        agent_wise_summary=agent_summaries,
        disposition_summary=disposition_summary,
    )
