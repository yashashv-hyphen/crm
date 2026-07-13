import uuid
import asyncio
from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_admin, get_current_user
from app.models.user import User
from app.schemas.ple import PleAgentSummaryRow, PleMcidDetailRow, PleMcidUpdateRequest
from app.schemas.upload import UploadInitResponse
from app.services import ple_service
from app.services.upload_service import get_dev_temp_path
from app.config import settings

router = APIRouter(prefix="/api/ple", tags=["ple"])


def _run_launches(upload_file_id: str) -> None:
    from app.tasks.ple_upload_task import process_ple_launches_upload
    process_ple_launches_upload.apply(args=[upload_file_id])


def _run_mcid_detail(upload_file_id: str) -> None:
    from app.tasks.ple_upload_task import process_ple_mcid_upload
    process_ple_mcid_upload.apply(args=[upload_file_id])


async def _bg(fn, upload_file_id: str) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, fn, upload_file_id)


async def _store_and_queue(
    file: UploadFile, upload_type: str, admin: User, db: AsyncSession,
    background_tasks: BackgroundTasks, run_fn,
) -> UploadInitResponse:
    from app.models.upload_file import UploadFile as UploadFileModel

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    upload_id = uuid.uuid4()
    s3_key = f"ple/{upload_id}/{file.filename}"

    if not settings.r2_bucket:
        path = get_dev_temp_path(str(upload_id))
        with open(path, "wb") as f:
            f.write(file_bytes)
    else:
        from app.services.s3_service import upload_file_to_s3
        upload_file_to_s3(file_bytes, s3_key)

    record = UploadFileModel(
        id=upload_id,
        admin_id=admin.id,
        filename=file.filename,
        s3_key=s3_key,
        upload_type=upload_type,
        status="pending",
    )
    db.add(record)
    await db.commit()

    background_tasks.add_task(_bg, run_fn, str(upload_id))
    return UploadInitResponse(upload_id=upload_id, task_id=str(upload_id), message="PLE upload queued for processing")


@router.post("/upload/launches", response_model=UploadInitResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_ple_launches(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if not file.filename or not file.filename.lower().endswith(".xlsb"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .xlsb files are accepted")
    return await _store_and_queue(file, "ple_launches", admin, db, background_tasks, _run_launches)


@router.post("/upload/mcid-detail", response_model=UploadInitResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_ple_mcid_detail(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .xlsx files are accepted")
    return await _store_and_queue(file, "ple_mcid_detail", admin, db, background_tasks, _run_mcid_detail)


@router.get("/agent-summary", response_model=list[PleAgentSummaryRow])
async def agent_summary(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return await ple_service.get_agent_summary(db)


@router.get("/mcid-detail", response_model=list[PleMcidDetailRow])
async def mcid_detail(
    agent_user_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # FOS users only see their own MCIDs; admins see everything, or one agent via ?agent_user_id=.
    filter_agent_user_id = current_user.id if current_user.role == "fos" else agent_user_id
    return await ple_service.get_mcid_detail(db, agent_user_id=filter_agent_user_id)


@router.patch("/mcid/{mcid}", response_model=PleMcidDetailRow)
async def update_mcid(
    mcid: str,
    body: PleMcidUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await ple_service.update_mcid_record(db, mcid, body, current_user)
    await db.commit()
    return result


@router.get("/mcid/{mcid}/history")
async def mcid_history(
    mcid: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ple_service.get_mcid_history(db, mcid, current_user)
