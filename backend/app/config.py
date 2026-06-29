from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://redis:6379/0"
    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 4

    # Cloudflare R2 (S3-compatible file storage)
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_endpoint_url: str = ""  # https://<account_id>.r2.cloudflarestorage.com
    r2_bucket: str = ""

    # Brevo SMTP (email)
    smtp_host: str = "smtp-relay.brevo.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = "noreply@newtrendscommerce.in"

    allowed_email_domain: str = "newtrendscommerce.in"
    allowed_origins: str = ""  # comma-separated, e.g. https://myapp.up.railway.app
    environment: str = "development"
    secure_cookies: bool = False  # set True in production (HTTPS)

    class Config:
        env_file = ".env"


settings = Settings()
