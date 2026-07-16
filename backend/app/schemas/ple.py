import uuid
from datetime import date, datetime
from pydantic import BaseModel


class PleAgentSummaryRow(BaseModel):
    agent: str
    agent_user_id: uuid.UUID | None
    num_launches: int
    fba_status_count: int
    fba_live_selection: int
    sp_status_count: int
    cp_adoption_count: int
    narf_cross_launch_count: int
    buyable_asin: int


class PleMcidDetailRow(BaseModel):
    id: uuid.UUID
    mcid: str
    agent_name: str | None
    agent_user_id: uuid.UUID | None
    marketplace_id: str | None

    # Launches-file fields
    fba_status: str | None
    fba_live_selection: int | None
    sp_status: str | None
    cp_adoption: str | None
    narf_cross_launch: str | None
    buyable_asin: int | None
    launch_yn: str | None
    sp_yn: str | None
    coupons_yn: str | None
    cross_launch_final_stage: str | None

    # Working-file (MCID detail) fields
    launch_date: date | None
    launch_week: str | None
    fba_launch_date: date | None
    fba_launch_week: str | None
    sp_launch_date: date | None
    sp_launch_week: str | None
    sp_spend: float | None
    cp_launch_date: date | None
    coupon_launch_week: str | None
    cl_status: str | None
    total_live_selection: int | None
    fba_live_selection_wf: int | None
    total_gms: float | None
    fba_gms: float | None
    swas: float | None
    fba_swas: float | None
    fba_intransit: int | None

    lead_id: uuid.UUID | None
    launches_uploaded_at: datetime | None
    mcid_uploaded_at: datetime | None
    updated_at: datetime

    # From the matching Lead (by merchant_id == mcid), if one exists —
    # lets call-upload data surface anywhere PLE data is shown.
    call_count: int | None = None
    total_call_time: float | None = None

    model_config = {"from_attributes": True}


class PleMcidUpdateRequest(BaseModel):
    fba_status: str | None = None
    sp_status: str | None = None
    cl_status: str | None = None
    cp_adoption: str | None = None
    narf_cross_launch: str | None = None
    launch_yn: str | None = None
    sp_yn: str | None = None
    coupons_yn: str | None = None
    cross_launch_final_stage: str | None = None
    launch_date: date | None = None
    fba_launch_date: date | None = None
    sp_launch_date: date | None = None
    cp_launch_date: date | None = None


class PleRecordHistoryEntry(BaseModel):
    field_name: str
    old_value: str | None
    new_value: str | None
    performed_by_name: str | None
    performed_at: datetime

    model_config = {"from_attributes": True}
