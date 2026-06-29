import uuid
from pydantic import BaseModel


class StageSummaryRow(BaseModel):
    activity_id: uuid.UUID
    activity_name: str
    total_assigned: int
    moved_to_next: int
    pending: int


class DispositionSummaryRow(BaseModel):
    sub_disposition: str
    this_week: int
    ytd: int


class FOSDashboardResponse(BaseModel):
    stage_summary: list[StageSummaryRow]
    disposition_summary: list[DispositionSummaryRow]
    follow_up_today_count: int


class AgentStageSummary(BaseModel):
    fos_id: uuid.UUID
    fos_name: str
    stage_summary: list[StageSummaryRow]


class AdminDashboardResponse(BaseModel):
    overall_stage_summary: list[StageSummaryRow]
    agent_wise_summary: list[AgentStageSummary]
    disposition_summary: list[DispositionSummaryRow]
