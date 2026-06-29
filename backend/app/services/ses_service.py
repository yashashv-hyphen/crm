import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

logger = logging.getLogger(__name__)


def _send_email(to_email: str, subject: str, body: str) -> None:
    if settings.environment == "development" or not settings.smtp_user:
        logger.info("[DEV] Email to %s | Subject: %s | Body: %s", to_email, subject, body)
        return

    msg = MIMEMultipart()
    msg["From"] = settings.from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.from_email, to_email, msg.as_string())


def send_otp_email(to_email: str, otp_code: str) -> None:
    _send_email(
        to_email=to_email,
        subject="Your CRM Login OTP",
        body=(
            f"Your CRM OTP is {otp_code} — valid for 10 minutes.\n\n"
            "Do not share this OTP with anyone."
        ),
    )


def send_welcome_email(to_email: str, full_name: str) -> None:
    _send_email(
        to_email=to_email,
        subject="Welcome to Global Sales CRM",
        body=(
            f"Hi {full_name},\n\n"
            "You have been added to Global Sales CRM.\n"
            "Login using your email and OTP.\n\n"
            "Your OTP will be sent to this email address each time you login."
        ),
    )
