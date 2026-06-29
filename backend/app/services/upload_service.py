import uuid
import os
import tempfile
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.upload_file import UploadFile
from app.models.user import User
from app.services.s3_service import upload_file_to_s3
from app.utils.excel_validator import validate_template1_pre_upload, validate_template2_pre_upload
from app.config import settings

_DEV_TEMP_DIR = tempfile.gettempdir()


def get_dev_temp_path(upload_id: str) -> str:
    return os.path.join(_DEV_TEMP_DIR, f"crm_upload_{upload_id}.xlsx")


async def create_upload_record(
    file_bytes: bytes,
    filename: str,
    activity_id: uuid.UUID | None,
    upload_type: str,
    admin: User,
    db: AsyncSession,
) -> UploadFile:
    # Stage 1 validation
    if upload_type == "template1":
        errors = validate_template1_pre_upload(file_bytes)
    else:
        errors = validate_template2_pre_upload(file_bytes)

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": errors},
        )

    upload_id = uuid.uuid4()
    s3_key = f"{upload_type}/{upload_id}/{filename}"

    if settings.r2_bucket:
        upload_file_to_s3(file_bytes, s3_key)
    else:
        # Local fallback (dev or when R2 not configured)
        temp_path = get_dev_temp_path(str(upload_id))
        with open(temp_path, "wb") as f:
            f.write(file_bytes)

    record = UploadFile(
        id=upload_id,
        activity_id=activity_id,
        admin_id=admin.id,
        filename=filename,
        s3_key=s3_key,
        upload_type=upload_type,
        status="pending",
    )
    db.add(record)
    await db.flush()
    return record
