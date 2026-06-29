import uuid
from datetime import datetime
from pydantic import BaseModel


class SubDispositionResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_common: bool
    activity_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class SubDispositionCreate(BaseModel):
    name: str
    is_common: bool = False


class ActivityCreate(BaseModel):
    name: str
    position_order: int | None = None


class ActivityResponse(BaseModel):
    id: uuid.UUID
    name: str
    position_order: int
    is_active: bool
    created_at: datetime
    sub_dispositions: list[SubDispositionResponse] = []

    model_config = {"from_attributes": True}


class ActivityReorderItem(BaseModel):
    id: uuid.UUID
    position_order: int


class ActivityReorderRequest(BaseModel):
    items: list[ActivityReorderItem]
