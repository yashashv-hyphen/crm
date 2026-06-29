import uuid
from pydantic import BaseModel


class PerformanceStageMetric(BaseModel):
    activity_name: str
    total_assigned: int
    total_moved: int
    movement_pct: float
    avg_days_in_stage: float | None


class PerformanceReportRow(BaseModel):
    fos_id: uuid.UUID
    fos_name: str
    metrics: list[PerformanceStageMetric]
    overall_avg_days: float | None


class PerformanceReportResponse(BaseModel):
    rows: list[PerformanceReportRow]
    totals: PerformanceReportRow | None
