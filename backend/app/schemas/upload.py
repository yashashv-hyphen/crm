import uuid
from datetime import datetime
from pydantic import BaseModel


class UploadInitResponse(BaseModel):
    upload_id: uuid.UUID
    task_id: str
    message: str


class UploadStatusResponse(BaseModel):
    upload_id: uuid.UUID
    status: str
    total_rows: int | None
    success_rows: int | None
    error_rows: int | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class UploadErrorRow(BaseModel):
    row_number: int
    merchant_id: str | None
    error_type: str
    error_detail: str

    model_config = {"from_attributes": True}


class UploadErrorReport(BaseModel):
    upload_id: uuid.UUID
    errors: list[UploadErrorRow]
    total_errors: int
