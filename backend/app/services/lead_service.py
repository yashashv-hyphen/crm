import uuid
import io
from datetime import date, datetime, timezone
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from fastapi import HTTPException, status
from openpyxl import Workbook

from app.models.lead import Lead
from app.models.lead_history import LeadHistory
from app.models.lead_assignment import LeadAssignment
from app.models.user import User
from app.models.activity import Activity
from app.services import stage_bucketing
from app.schemas.lead import (
    LeadResponse, LeadUpdateRequest, LeadFilters,
    BulkUpdateRequest, PaginatedLeads,
)
from app.utils.pagination import paginate


def get_aging_color(entry_date: date | None) -> str | None:
    if entry_date is None:
        return None
    days = (date.today() - entry_date).days
    if days <= 7:
        return "green"
    elif days <= 14:
        return "yellow"
    elif days <= 21:
        return "orange"
    return "red"


def get_follow_up_status(follow_up_date: date | None) -> str | None:
    if follow_up_date is None:
        return None
    today = date.today()
    if follow_up_date < today:
        return "overdue"
    elif follow_up_date == today:
        return "today"
    elif (follow_up_date - today).days <= 7:
        return "upcoming"
    return "future"


async def _get_fos_name(fos_id: uuid.UUID | None, db: AsyncSession) -> str | None:
    if fos_id is None:
        return None
    result = await db.execute(select(User.full_name).where(User.id == fos_id))
    return result.scalar_one_or_none()


async def _get_current_entry_date(lead: Lead, db: AsyncSession) -> date | None:
    if lead.current_activity_id is None:
        return None
    result = await db.execute(select(Activity.name).where(Activity.id == lead.current_activity_id))
    name = result.scalar_one_or_none()
    if not name:
        return None
    name_lower = name.lower()
    if "rnc" in name_lower:
        return lead.rnc_entry_date
    elif "idv" in name_lower:
        return lead.idv_entry_date
    elif "rtl" in name_lower:
        return lead.rtl_entry_date
    elif "fba" in name_lower:
        return lead.fba_entry_date
    elif "sp " in name_lower or name_lower == "sp pending":
        return lead.sp_entry_date
    elif "open spending" in name_lower or "coupon" in name_lower:
        return lead.open_spending_entry_date
    elif "narf" in name_lower:
        return lead.narf_entry_date
    elif "gsi" in name_lower:
        return lead.gsi_entry_date
    return lead.created_at.date() if lead.created_at else None


async def enrich_lead(lead: Lead, db: AsyncSession) -> LeadResponse:
    fos_name = await _get_fos_name(lead.assigned_fos_id, db)
    entry_date = await _get_current_entry_date(lead, db)
    aging_color = get_aging_color(entry_date)
    follow_up_status = get_follow_up_status(lead.follow_up_date)

    data = LeadResponse.model_validate(lead)
    data.assigned_fos_name = fos_name
    data.aging_color = aging_color
    data.follow_up_status = follow_up_status
    if entry_date:
        data.aging_days = (date.today() - entry_date).days
    return data


def _build_lead_query(filters: LeadFilters, user: User):
    query = select(Lead).where(Lead.is_archived == filters.is_archived)

    if user.role == "fos":
        query = query.where(Lead.assigned_fos_id == user.id)
    else:
        if filters.fos_id:
            query = query.where(Lead.assigned_fos_id == filters.fos_id)

    if filters.activity_id:
        query = query.where(Lead.current_activity_id == filters.activity_id)
    if filters.current_stage:
        query = query.where(Lead.current_stage == filters.current_stage)
    if filters.assigned_stage_bucket:
        query = query.where(stage_bucketing.assigned_stage_condition(filters.assigned_stage_bucket))
    if filters.current_stage_bucket:
        query = query.where(stage_bucketing.current_stage_condition(filters.current_stage_bucket))
    if filters.sub_disposition:
        query = query.where(Lead.sub_disposition == filters.sub_disposition)
    if filters.follow_up_date:
        query = query.where(Lead.follow_up_date == filters.follow_up_date)
    if filters.week_no:
        query = query.where(Lead.week_no == filters.week_no)
    if filters.year:
        query = query.where(Lead.year == filters.year)
    if filters.from_date:
        query = query.where(Lead.date_of_assignment >= filters.from_date)
    if filters.to_date:
        query = query.where(Lead.date_of_assignment <= filters.to_date)
    if filters.upload_file_id:
        query = query.where(Lead.source_upload_id == filters.upload_file_id)

    return query.order_by(Lead.created_at.desc())


async def get_leads(
    filters: LeadFilters,
    page: int,
    size: int,
    user: User,
    db: AsyncSession,
) -> PaginatedLeads:
    query = _build_lead_query(filters, user)
    items, total = await paginate(db, query, page, size)
    enriched = [await enrich_lead(lead, db) for lead in items]
    pages = (total + size - 1) // size if size else 1
    return PaginatedLeads(items=enriched, total=total, page=page, size=size, pages=pages)


async def update_lead(
    lead_id: uuid.UUID,
    data: LeadUpdateRequest,
    user: User,
    db: AsyncSession,
) -> LeadResponse:
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    if user.role == "fos" and lead.assigned_fos_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your lead")

    update_data = data.model_dump(exclude_unset=True)
    for field, new_value in update_data.items():
        old_value = getattr(lead, field, None)
        if old_value != new_value:
            history = LeadHistory(
                id=uuid.uuid4(),
                lead_id=lead.id,
                action_type=field,
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(new_value) if new_value is not None else None,
                performed_by=user.id,
            )
            db.add(history)
            setattr(lead, field, new_value)

    lead.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return await enrich_lead(lead, db)


async def bulk_update_leads(
    request: BulkUpdateRequest,
    user: User,
    db: AsyncSession,
) -> dict:
    result = await db.execute(select(Lead).where(Lead.id.in_(request.lead_ids)))
    leads = result.scalars().all()

    for lead in leads:
        if user.role == "fos" and lead.assigned_fos_id != user.id:
            continue

        if request.sub_disposition is not None:
            old = lead.sub_disposition
            lead.sub_disposition = request.sub_disposition
            db.add(LeadHistory(
                id=uuid.uuid4(), lead_id=lead.id, action_type="sub_disposition",
                old_value=old, new_value=request.sub_disposition, performed_by=user.id,
            ))

        if request.follow_up_date is not None:
            old = str(lead.follow_up_date) if lead.follow_up_date else None
            lead.follow_up_date = request.follow_up_date
            db.add(LeadHistory(
                id=uuid.uuid4(), lead_id=lead.id, action_type="follow_up_date",
                old_value=old, new_value=str(request.follow_up_date), performed_by=user.id,
            ))

        if user.role == "admin":
            if request.assign_to_fos_id is not None:
                old_fos = lead.assigned_fos_id
                db.add(LeadAssignment(
                    id=uuid.uuid4(), lead_id=lead.id,
                    from_fos_id=old_fos, to_fos_id=request.assign_to_fos_id,
                    assigned_by=user.id,
                ))
                lead.assigned_fos_id = request.assign_to_fos_id
                lead.follow_up_date = None
                db.add(LeadHistory(
                    id=uuid.uuid4(), lead_id=lead.id, action_type="reassignment",
                    old_value=str(old_fos), new_value=str(request.assign_to_fos_id),
                    performed_by=user.id,
                ))

            if request.archive is True:
                lead.is_archived = True
                lead.archive_year = request.archive_year or date.today().year

        lead.updated_at = datetime.now(timezone.utc)

    await db.flush()
    return {"updated": len(leads)}


def leads_to_excel(leads: list[Lead]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Leads"

    headers = [
        "Merchant ID", "Seller Name", "Mobile Number", "Email ID",
        "Stage Assigned", "Date of Assignment", "Week No", "Year",
        "Current Stage", "Sub Disposition", "Final Stage",
        "Assigned FOS", "Remark", "Follow Up Date",
        "RNC Entry Date", "IDV Entry Date", "RTL Entry Date",
        "FBA Entry Date", "SP Entry Date", "Open Spending Entry Date",
        "NARF Entry Date", "GSI Entry Date",
        "Is Archived", "Archive Year", "Created At", "Updated At",
    ]
    ws.append(headers)

    for lead in leads:
        ws.append([
            lead.merchant_id, lead.seller_name, lead.mobile_number, lead.email_id,
            lead.stage_assigned, lead.date_of_assignment, lead.week_no, lead.year,
            lead.current_stage, lead.sub_disposition, lead.final_stage,
            str(lead.assigned_fos_id) if lead.assigned_fos_id else None,
            lead.remark, lead.follow_up_date,
            lead.rnc_entry_date, lead.idv_entry_date, lead.rtl_entry_date,
            lead.fba_entry_date, lead.sp_entry_date, lead.open_spending_entry_date,
            lead.narf_entry_date, lead.gsi_entry_date,
            lead.is_archived, lead.archive_year,
            lead.created_at, lead.updated_at,
        ])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
