import io
import uuid
from datetime import date
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.report import PerformanceReportResponse
from app.services import report_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/performance", response_model=PerformanceReportResponse)
async def performance_report(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    fos_id: uuid.UUID | None = Query(default=None),
    year: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # FOS can only see their own data
    if current_user.role == "fos":
        fos_id = current_user.id
    return await report_service.get_performance_report(from_date, to_date, fos_id, year, db)


@router.get("/performance/download")
async def download_performance_report(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    fos_id: uuid.UUID | None = Query(default=None),
    year: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "fos":
        fos_id = current_user.id
    report = await report_service.get_performance_report(from_date, to_date, fos_id, year, db)
    excel_bytes = report_service.export_report_to_excel(report)
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=performance_report.xlsx"},
    )
