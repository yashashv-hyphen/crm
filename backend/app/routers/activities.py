import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.models.activity import Activity
from app.models.sub_disposition import SubDisposition
from app.models.lead import Lead
from app.schemas.activity import (
    ActivityCreate, ActivityResponse, ActivityReorderRequest,
    SubDispositionCreate, SubDispositionResponse,
)

router = APIRouter(prefix="/api/activities", tags=["activities"])


async def _build_activity_response(activity: Activity, db: AsyncSession) -> ActivityResponse:
    sd_result = await db.execute(
        select(SubDisposition)
        .where(
            (SubDisposition.activity_id == activity.id) | (SubDisposition.is_common == True),  # noqa: E712
            SubDisposition.is_active == True,  # noqa: E712
        )
    )
    sub_dispositions = sd_result.scalars().all()
    data = ActivityResponse.model_validate(activity)
    data.sub_dispositions = [SubDispositionResponse.model_validate(sd) for sd in sub_dispositions]
    return data


@router.get("", response_model=list[ActivityResponse])
async def list_activities(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Activity)
        .where(Activity.is_active == True)  # noqa: E712
        .order_by(Activity.position_order)
    )
    activities = result.scalars().all()
    return [await _build_activity_response(a, db) for a in activities]


@router.post("", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    body: ActivityCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    if body.position_order is None:
        max_result = await db.execute(select(func.max(Activity.position_order)))
        max_order = max_result.scalar() or 0
        position_order = max_order + 1
    else:
        position_order = body.position_order

    activity = Activity(id=uuid.uuid4(), name=body.name, position_order=position_order)
    db.add(activity)
    await db.flush()
    return await _build_activity_response(activity, db)


@router.post("/reorder")
async def reorder_activities(
    body: ActivityReorderRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    for item in body.items:
        result = await db.execute(select(Activity).where(Activity.id == item.id))
        activity = result.scalar_one_or_none()
        if activity:
            activity.position_order = item.position_order
    await db.flush()
    return {"message": "Activities reordered"}


@router.patch("/{activity_id}")
async def update_activity(
    activity_id: uuid.UUID,
    body: ActivityCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    if body.name:
        activity.name = body.name
    await db.flush()
    return await _build_activity_response(activity, db)


@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    lead_count_result = await db.execute(
        select(func.count()).where(
            Lead.current_activity_id == activity_id,
            Lead.is_archived == False,  # noqa: E712
        )
    )
    lead_count = lead_count_result.scalar() or 0
    if lead_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete activity with {lead_count} active leads",
        )

    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    activity.is_active = False
    await db.flush()
    return {"message": "Activity deactivated"}


@router.get("/{activity_id}/sub-dispositions", response_model=list[SubDispositionResponse])
async def get_sub_dispositions(
    activity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SubDisposition).where(
            ((SubDisposition.activity_id == activity_id) | (SubDisposition.is_common == True)),  # noqa: E712
            SubDisposition.is_active == True,  # noqa: E712
        )
    )
    return result.scalars().all()


@router.post("/{activity_id}/sub-dispositions", response_model=SubDispositionResponse, status_code=status.HTTP_201_CREATED)
async def create_sub_disposition(
    activity_id: uuid.UUID,
    body: SubDispositionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    sd = SubDisposition(
        id=uuid.uuid4(),
        activity_id=None if body.is_common else activity_id,
        name=body.name,
        is_common=body.is_common,
    )
    db.add(sd)
    await db.flush()
    return sd


@router.delete("/sub-dispositions/{sd_id}")
async def delete_sub_disposition(
    sd_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    active_leads_result = await db.execute(
        select(func.count()).where(Lead.sub_disposition == str(sd_id))
    )
    if (active_leads_result.scalar() or 0) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete sub-disposition that is currently used on active leads",
        )

    result = await db.execute(select(SubDisposition).where(SubDisposition.id == sd_id))
    sd = result.scalar_one_or_none()
    if not sd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sub-disposition not found")
    sd.is_active = False
    await db.flush()
    return {"message": "Sub-disposition deleted"}
