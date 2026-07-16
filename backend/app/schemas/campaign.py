import uuid
from datetime import datetime
from pydantic import BaseModel
from app.schemas.lead import LeadResponse


class CampaignOut(BaseModel):
    id: uuid.UUID
    name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignLeadOut(BaseModel):
    campaign_id: uuid.UUID
    campaign_name: str
    event_remark: str | None
    lead: LeadResponse
