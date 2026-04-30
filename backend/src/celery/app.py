from celery import Celery
from src.celery.config import settings

celery_app = Celery(
    "story_app",
    broker=settings.BROKER_URL,
    backend=settings.RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.TIMEZONE,
    enable_utc=settings.ENABLE_UTC,
)
celery_app.conf.beat_schedule = {
    "cleanup-stories-every-10-min": {
        "task": "src.celery.tasks.story_tasks.cleanup_expired_stories",
        "schedule": 600.0,  # 10 minutes
    }
}

# auto-discover tasks
celery_app.autodiscover_tasks(["src.celery.tasks"])