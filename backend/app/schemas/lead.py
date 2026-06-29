import uuid
from datetime import datetime, date
from pydantic import BaseModel


class LeadHistoryEntry(BaseModel):
    action_type: str
    old_value: str | None
    new_value: str | None
    performed_by_name: str | None
    performed_at: datetime

    model_config = {"from_attributes": True}


class LeadResponse(BaseModel):
    id: uuid.UUID
    merchant_id: str
    seller_name: str | None
    mobile_number: str | None
    alternate_phone: str | None = None
    email_id: str | None
    stage_assigned: str | None
    date_of_assignment: date | None
    week_no: int | None
    year: int | None
    current_activity_id: uuid.UUID | None
    current_stage: str | None
    sub_disposition: str | None
    final_stage: str | None
    assigned_fos_id: uuid.UUID | None
    assigned_fos_name: str | None = None
    remark: str | None
    follow_up_date: date | None
    rnc_entry_date: date | None
    idv_entry_date: date | None
    rtl_entry_date: date | None
    fba_entry_date: date | None
    sp_entry_date: date | None
    open_spending_entry_date: date | None
    narf_entry_date: date | None
    gsi_entry_date: date | None
    custom_data: dict | None
    is_archived: bool
    archive_year: int | None
    aging_days: int | None = None
    aging_color: str | None = None
    follow_up_status: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadUpdateRequest(BaseModel):
    current_stage: str | None = None
    sub_disposition: str | None = None
    remark: str | None = None
    follow_up_date: date | None = None
    alternate_phone: str | None = None
    custom_data: dict | None = None


class LeadFilters(BaseModel):
    activity_id: uuid.UUID | None = None
    fos_id: uuid.UUID | None = None
    current_stage: str | None = None
    sub_disposition: str | None = None
    follow_up_date: date | None = None
    aging_color: str | None = None
    week_no: int | None = None
    year: int | None = None
    is_archived: bool = False
    from_date: date | None = None
    to_date: date | None = None
    upload_file_id: uuid.UUID | None = None


class BulkUpdateRequest(BaseModel):
    lead_ids: list[uuid.UUID]
    sub_disposition: str | None = None
    follow_up_date: date | None = None
    assign_to_fos_id: uuid.UUID | None = None  # admin only
    archive: bool | None = None  # admin only
    archive_year: int | None = None


class PaginatedLeads(BaseModel):
    items: list[LeadResponse]
    total: int
    page: int
    size: int
    pages: int
