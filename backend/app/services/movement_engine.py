import uuid
from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.activity import Activity
from app.models.lead import Lead
from app.models.lead_history import LeadHistory
from app.models.user import User

ACTIVITY_ENTRY_DATE_MAP: dict[str, str] = {
    "rnc": "rnc_entry_date",
    "idv": "idv_entry_date",
    "rtl": "rtl_entry_date",
    "fba": "fba_entry_date",
    "sp": "sp_entry_date",
    "open spending": "open_spending_entry_date",
    "narf": "narf_entry_date",
    "gsi": "gsi_entry_date",
}


def _activity_entry_field(activity_name: str) -> str | None:
    name_lower = activity_name.lower()
    for key, field in ACTIVITY_ENTRY_DATE_MAP.items():
        if key in name_lower:
            return field
    return None


async def get_next_activity(current_activity_id: uuid.UUID, db: AsyncSession) -> Activity | None:
    current_result = await db.execute(
        select(Activity.position_order).where(Activity.id == current_activity_id)
    )
    current_order = current_result.scalar_one_or_none()
    if current_order is None:
        return None

    next_result = await db.execute(
        select(Activity)
        .where(Activity.position_order > current_order, Activity.is_active == True)  # noqa: E712
        .order_by(Activity.position_order.asc())
        .limit(1)
    )
    return next_result.scalar_one_or_none()


async def move_lead_to_next_activity(
    lead: Lead,
    final_stage: str,
    week_no: int,
    year: int,
    uploaded_by: User,
    db: AsyncSession,
) -> bool:
    """Move lead to next activity. Returns True if moved, False if no next activity."""
    if lead.current_activity_id is None:
        return False

    next_activity = await get_next_activity(lead.current_activity_id, db)
    if next_activity is None:
        # Lead is at the last activity — update final stage only
        old_final = lead.final_stage
        lead.final_stage = final_stage
        lead.week_of_movement = week_no
        db.add(LeadHistory(
            id=uuid.uuid4(),
            lead_id=lead.id,
            action_type="final_stage_update",
            old_value=old_final,
            new_value=final_stage,
            performed_by=uploaded_by.id,
        ))
        lead.updated_at = datetime.now(timezone.utc)
        return False

    old_activity_id = lead.current_activity_id

    # Set entry date for next activity
    entry_field = _activity_entry_field(next_activity.name)
    if entry_field:
        setattr(lead, entry_field, date.today())

    lead.current_activity_id = next_activity.id
    lead.current_stage = next_activity.name
    lead.final_stage = final_stage
    lead.week_of_movement = week_no
    lead.sub_disposition = None
    lead.follow_up_date = None
    lead.updated_at = datetime.now(timezone.utc)

    db.add(LeadHistory(
        id=uuid.uuid4(),
        lead_id=lead.id,
        action_type="movement",
        old_value=str(old_activity_id),
        new_value=str(next_activity.id),
        performed_by=uploaded_by.id,
    ))
    return True
