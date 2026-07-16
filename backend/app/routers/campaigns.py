import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.models.campaign import Campaign, CampaignLead
from app.models.lead import Lead
from app.schemas.campaign import CampaignOut, CampaignLeadOut
from app.services import lead_service
from app.services.upload_service import get_dev_temp_path
from app.config import settings

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.get("", response_model=list[CampaignOut])
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Campaign).order_by(Campaign.created_at.desc()))
    return result.scalars().all()


@router.post("/{campaign_id}/toggle", response_model=CampaignOut)
async def toggle_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.is_active = not campaign.is_active
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.post("/upload", response_model=CampaignOut)
async def upload_campaign(
    name: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    from app.models.upload_file import UploadFile as UploadFileModel
    from app.tasks.campaign_upload_task import process_campaign_upload
    import tempfile, os

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    # Create campaign
    campaign = Campaign(
        id=uuid.uuid4(),
        name=name.strip(),
        created_by=current_user.id,
    )
    db.add(campaign)
    await db.flush()

    # Store file + create upload record
    upload_id = str(uuid.uuid4())
    s3_key = f"campaigns/{upload_id}/{file.filename}"

    if not settings.r2_bucket:
        path = get_dev_temp_path(upload_id)
        with open(path, "wb") as f:
            f.write(file_bytes)
    else:
        from app.services.s3_service import upload_file_to_s3
        upload_file_to_s3(file_bytes, s3_key)

    upload_record = UploadFileModel(
        id=uuid.UUID(upload_id),
        admin_id=current_user.id,
        filename=file.filename,
        s3_key=s3_key,
        upload_type="campaign",
        status="pending",
    )
    db.add(upload_record)
    await db.commit()

    process_campaign_upload.delay(upload_id, str(campaign.id))
    return campaign


@router.get("/leads", response_model=list[CampaignLeadOut])
async def get_my_campaign_leads(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(CampaignLead, Campaign)
        .join(Campaign, CampaignLead.campaign_id == Campaign.id)
        .join(Lead, CampaignLead.lead_id == Lead.id)
        .where(Campaign.is_active == True)  # noqa: E712
    )
    if current_user.role == "fos":
        query = query.where(Lead.assigned_fos_id == current_user.id)

    result = await db.execute(query)
    rows = result.all()

    out = []
    for cl, camp in rows:
        lead_result = await db.execute(select(Lead).where(Lead.id == cl.lead_id))
        lead = lead_result.scalar_one_or_none()
        if not lead:
            continue
        enriched = await lead_service.enrich_lead(lead, db)
        out.append(CampaignLeadOut(
            campaign_id=camp.id,
            campaign_name=camp.name,
            event_remark=cl.event_remark,
            lead=enriched,
        ))
    return out
