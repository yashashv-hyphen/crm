import uuid
import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.models.upload_file import UploadFile as UploadFileModel
from app.models.upload_error import UploadError
from app.schemas.upload import UploadInitResponse, UploadStatusResponse, UploadErrorReport, UploadErrorRow
from app.services.upload_service import create_upload_record
from app.tasks.excel_upload_task import process_template1_upload, process_template2_upload

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


def _run_t1(upload_file_id: str) -> None:
    process_template1_upload.apply(args=[upload_file_id])


def _run_t2(upload_file_id: str) -> None:
    process_template2_upload.apply(args=[upload_file_id])


async def _bg(fn, upload_file_id: str) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, fn, upload_file_id)


@router.post("/template1", response_model=UploadInitResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_template1(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    activity_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .xlsx files are accepted")

    file_bytes = await file.read()
    act_id = uuid.UUID(activity_id)

    record = await create_upload_record(
        file_bytes=file_bytes,
        filename=file.filename,
        activity_id=act_id,
        upload_type="template1",
        admin=admin,
        db=db,
    )
    await db.commit()

    background_tasks.add_task(_bg, _run_t1, str(record.id))

    return UploadInitResponse(upload_id=record.id, task_id=str(record.id), message="Upload queued for processing")


@router.post("/template2", response_model=UploadInitResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_template2(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .xlsx files are accepted")

    file_bytes = await file.read()

    record = await create_upload_record(
        file_bytes=file_bytes,
        filename=file.filename,
        activity_id=None,
        upload_type="template2",
        admin=admin,
        db=db,
    )
    await db.commit()

    background_tasks.add_task(_bg, _run_t2, str(record.id))

    return UploadInitResponse(upload_id=record.id, task_id=str(record.id), message="Final stage upload queued")


@router.get("/{upload_id}/status", response_model=UploadStatusResponse)
async def get_upload_status(
    upload_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(UploadFileModel).where(UploadFileModel.id == upload_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")
    return record


@router.get("/{upload_id}/errors", response_model=UploadErrorReport)
async def get_upload_errors(
    upload_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(
        select(UploadError)
        .where(UploadError.upload_file_id == upload_id)
        .order_by(UploadError.row_number)
    )
    errors = result.scalars().all()
    return UploadErrorReport(
        upload_id=upload_id,
        errors=[UploadErrorRow.model_validate(e) for e in errors],
        total_errors=len(errors),
    )
