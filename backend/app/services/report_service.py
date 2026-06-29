import io
import uuid
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from openpyxl import Workbook

from app.models.lead import Lead
from app.models.activity import Activity
from app.models.user import User
from app.schemas.report import (
    PerformanceReportResponse, PerformanceReportRow, PerformanceStageMetric,
)

ENTRY_DATE_PAIRS = [
    ("rnc", "rnc_entry_date", "idv_entry_date"),
    ("idv", "idv_entry_date", "rtl_entry_date"),
    ("rtl", "rtl_entry_date", "fba_entry_date"),
    ("fba", "fba_entry_date", "sp_entry_date"),
    ("sp", "sp_entry_date", "open_spending_entry_date"),
    ("open spending", "open_spending_entry_date", "narf_entry_date"),
    ("narf", "narf_entry_date", "gsi_entry_date"),
    ("gsi", "gsi_entry_date", None),
]


def _get_next_entry_field(activity_name: str) -> str | None:
    name_lower = activity_name.lower()
    for key, _entry, next_entry in ENTRY_DATE_PAIRS:
        if key in name_lower:
            return next_entry
    return None


def _get_entry_field(activity_name: str) -> str | None:
    name_lower = activity_name.lower()
    for key, entry, _ in ENTRY_DATE_PAIRS:
        if key in name_lower:
            return entry
    return None


async def get_performance_report(
    from_date: date | None,
    to_date: date | None,
    fos_id: uuid.UUID | None,
    year: int | None,
    db: AsyncSession,
) -> PerformanceReportResponse:
    fos_result = await db.execute(
        select(User).where(User.role == "fos", User.is_active == True)  # noqa: E712
    )
    all_fos = fos_result.scalars().all()
    if fos_id:
        all_fos = [u for u in all_fos if u.id == fos_id]

    act_result = await db.execute(
        select(Activity).where(Activity.is_active == True).order_by(Activity.position_order)  # noqa: E712
    )
    activities = act_result.scalars().all()

    rows: list[PerformanceReportRow] = []

    for fos_user in all_fos:
        metrics: list[PerformanceStageMetric] = []
        total_days_sum = 0.0
        total_days_count = 0

        for act in activities:
            entry_field = _get_entry_field(act.name)
            next_entry_field = _get_next_entry_field(act.name)

            base_cond = [
                Lead.assigned_fos_id == fos_user.id,
                Lead.is_archived == False,  # noqa: E712
            ]
            if entry_field:
                base_cond.append(getattr(Lead, entry_field).isnot(None))
            if year:
                base_cond.append(Lead.year == year)
            if from_date:
                base_cond.append(Lead.date_of_assignment >= from_date)
            if to_date:
                base_cond.append(Lead.date_of_assignment <= to_date)

            total_result = await db.execute(select(func.count()).where(*base_cond))
            total = total_result.scalar() or 0

            moved = 0
            avg_days: float | None = None
            if next_entry_field:
                moved_cond = base_cond + [getattr(Lead, next_entry_field).isnot(None)]
                moved_result = await db.execute(select(func.count()).where(*moved_cond))
                moved = moved_result.scalar() or 0

                if entry_field and moved > 0:
                    avg_result = await db.execute(
                        select(
                            func.avg(
                                func.extract("epoch", getattr(Lead, next_entry_field)) -
                                func.extract("epoch", getattr(Lead, entry_field))
                            ) / 86400
                        ).where(*moved_cond)
                    )
                    avg_secs = avg_result.scalar()
                    if avg_secs is not None:
                        avg_days = round(float(avg_secs), 1)
                        total_days_sum += avg_days * moved
                        total_days_count += moved

            movement_pct = round((moved / total * 100), 1) if total > 0 else 0.0
            metrics.append(PerformanceStageMetric(
                activity_name=act.name,
                total_assigned=total,
                total_moved=moved,
                movement_pct=movement_pct,
                avg_days_in_stage=avg_days,
            ))

        overall_avg = round(total_days_sum / total_days_count, 1) if total_days_count else None
        rows.append(PerformanceReportRow(
            fos_id=fos_user.id,
            fos_name=fos_user.full_name,
            metrics=metrics,
            overall_avg_days=overall_avg,
        ))

    # Compute totals row
    totals: PerformanceReportRow | None = None
    if rows and activities:
        total_metrics = []
        for i, act in enumerate(activities):
            t_assigned = sum(r.metrics[i].total_assigned for r in rows if i < len(r.metrics))
            t_moved = sum(r.metrics[i].total_moved for r in rows if i < len(r.metrics))
            t_pct = round(t_moved / t_assigned * 100, 1) if t_assigned else 0.0
            total_metrics.append(PerformanceStageMetric(
                activity_name=act.name,
                total_assigned=t_assigned,
                total_moved=t_moved,
                movement_pct=t_pct,
                avg_days_in_stage=None,
            ))

        overall_avgs = [r.overall_avg_days for r in rows if r.overall_avg_days is not None]
        totals = PerformanceReportRow(
            fos_id=uuid.UUID(int=0),
            fos_name="TOTAL",
            metrics=total_metrics,
            overall_avg_days=round(sum(overall_avgs) / len(overall_avgs), 1) if overall_avgs else None,
        )

    return PerformanceReportResponse(rows=rows, totals=totals)


def export_report_to_excel(report: PerformanceReportResponse) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Performance Report"

    if not report.rows:
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    activity_names = [m.activity_name for m in report.rows[0].metrics]
    header = ["FOS Name"]
    for act in activity_names:
        header += [f"{act} - Assigned", f"{act} - Moved", f"{act} - %"]
    header.append("Overall Avg Days")
    ws.append(header)

    all_rows = report.rows + ([report.totals] if report.totals else [])
    for row in all_rows:
        r = [row.fos_name]
        for m in row.metrics:
            r += [m.total_assigned, m.total_moved, m.movement_pct]
        r.append(row.overall_avg_days)
        ws.append(r)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
