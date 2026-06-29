from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import SendOTPRequest, VerifyOTPRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import send_otp, verify_otp_and_get_user
from app.dependencies import create_access_token, get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/send-otp")
async def send_otp_endpoint(body: SendOTPRequest, db: AsyncSession = Depends(get_db)):
    await send_otp(body.email, db)
    return {"message": "OTP sent successfully"}


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp_endpoint(
    body: VerifyOTPRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user = await verify_otp_and_get_user(body.email, body.otp, db)
    token = create_access_token(str(user.id), user.role)
    from app.config import settings as _s
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=4 * 3600,
        samesite="lax",
        secure=_s.secure_cookies,
    )
    return TokenResponse(message="Login successful", role=user.role, full_name=user.full_name)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
