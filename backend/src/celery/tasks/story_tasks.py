import asyncio
from datetime import datetime, timezone
from loguru import logger
from sqlalchemy import delete
from src.database.models.story import Story
from src.celery.app import celery_app
from src.database.config import SessionLocal


@celery_app.task
def cleanup_expired_stories():
    """
    Periodic task to delete expired stories from database.
    """

    try:
        with SessionLocal() as db:
            with db.begin():

                stmt = delete(Story).where(
                    Story.expires_at <= datetime.now(timezone.utc)
                )

                result = db.execute(stmt)

        logger.info(f"[Celery] Deleted {result.rowcount} expired stories")

        return result.rowcount

    except Exception as e:
        logger.exception(f"[Celery Error] cleanup_expired_stories failed: {e}")
        return 0
