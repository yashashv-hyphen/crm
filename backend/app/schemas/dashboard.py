import uuid
from pydantic import BaseModel


class StageSummaryRow(BaseModel):
    activity_id: uuid.UUID | None
    activity_name: str
    total_assigned: int
    pending: int | None


class StageMatrixRow(BaseModel):
    assigned_stage: str
    cells: dict[str, int]


class StageMatrixResponse(BaseModel):
    stages: list[str]
    rows: list[StageMatrixRow]


class DispositionSummaryRow(BaseModel):
    sub_disposition: str
    this_week: int
    ytd: int


class FOSDashboardResponse(BaseModel):
    stage_summary: list[StageSummaryRow]
    stage_matrix: StageMatrixResponse
    disposition_summary: list[DispositionSummaryRow]
    follow_up_today_count: int


class AgentStageSummary(BaseModel):
    fos_id: uuid.UUID
    fos_name: str
    stage_summary: list[StageSummaryRow]


class AdminDashboardResponse(BaseModel):
    total_leads: int
    overall_stage_summary: list[StageSummaryRow]
    overall_stage_matrix: StageMatrixResponse
    agent_wise_summary: list[AgentStageSummary]
    disposition_summary: list[DispositionSummaryRow]
