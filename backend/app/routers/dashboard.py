import uuid
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.dashboard import FOSDashboardResponse, AdminDashboardResponse
from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/fos", response_model=FOSDashboardResponse)
async def fos_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await dashboard_service.get_fos_dashboard(current_user.id, db)


@router.get("/admin", response_model=AdminDashboardResponse)
async def admin_dashboard(
    year: int | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    fos_id: uuid.UUID | None = Query(default=None),
    activity_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await dashboard_service.get_admin_dashboard(
        year=year,
        from_date=from_date,
        to_date=to_date,
        fos_id=fos_id,
        activity_id=activity_id,
        db=db,
    )
