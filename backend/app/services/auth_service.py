import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import HTTPException, status

from app.models.user import User
from app.models.otp import OTP
from app.utils.otp_utils import generate_otp, hash_otp, verify_otp
from app.services.ses_service import send_otp_email
from app.config import settings

OTP_EXPIRY_MINUTES = 10
OTP_RATE_LIMIT_SECONDS = 60
OTP_MAX_ATTEMPTS = 3


def _validate_email_domain(email: str) -> None:
    if not email.endswith(f"@{settings.allowed_email_domain}"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only @{settings.allowed_email_domain} emails are allowed",
        )


async def send_otp(email: str, db: AsyncSession) -> None:
    _validate_email_domain(email)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not registered")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    # Rate limit: 60 seconds between OTP requests
    latest_otp_result = await db.execute(
        select(OTP).where(OTP.user_id == user.id).order_by(desc(OTP.created_at)).limit(1)
    )
    latest_otp = latest_otp_result.scalar_one_or_none()
    if latest_otp:
        elapsed = (datetime.now(timezone.utc) - latest_otp.created_at.replace(tzinfo=timezone.utc)).total_seconds()
        if elapsed < OTP_RATE_LIMIT_SECONDS:
            wait = int(OTP_RATE_LIMIT_SECONDS - elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {wait} seconds before requesting a new OTP",
            )

    otp_code = generate_otp()
    otp_record = OTP(
        id=uuid.uuid4(),
        user_id=user.id,
        otp_hash=hash_otp(otp_code),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )
    db.add(otp_record)
    await db.flush()

    send_otp_email(email, otp_code)


async def verify_otp_and_get_user(email: str, otp_code: str, db: AsyncSession) -> User:
    _validate_email_domain(email)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    otp_result = await db.execute(
        select(OTP)
        .where(OTP.user_id == user.id, OTP.used_at == None)  # noqa: E711
        .order_by(desc(OTP.created_at))
        .limit(1)
    )
    otp_record = otp_result.scalar_one_or_none()

    if not otp_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active OTP found")

    if otp_record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="OTP has expired. Request a new one.")

    if otp_record.attempts >= OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Too many wrong attempts. Please request a new OTP.",
        )

    if not verify_otp(otp_code, otp_record.otp_hash):
        otp_record.attempts += 1
        await db.flush()
        remaining = OTP_MAX_ATTEMPTS - otp_record.attempts
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Incorrect OTP. {remaining} attempt(s) remaining.",
        )

    otp_record.used_at = datetime.now(timezone.utc)
    await db.flush()
    return user
