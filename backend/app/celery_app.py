from celery import Celery
from app.config import settings

celery_app = Celery(
    "crm",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.excel_upload_task", "app.tasks.final_stage_task"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
