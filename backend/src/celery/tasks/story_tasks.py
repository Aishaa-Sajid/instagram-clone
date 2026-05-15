import asyncio
from datetime import datetime, timezone
from loguru import logger
from sqlalchemy import delete
from src.database.models.story import Story
from src.celery.celery_app import celery_app
from src.database.config import sessionmanager
from src.repositories.story_repo import delete_expired_stories


async def cleanup_expired_stories_async():
    async with sessionmanager.session() as db:
        return await delete_expired_stories(db)


@celery_app.task
def cleanup_expired_stories():
    try:
        count = asyncio.run(cleanup_expired_stories_async())
        logger.info(f"[Celery] Deleted {count} expired stories")
        return count
    except Exception as e:
        logger.exception(f"[Celery Error] cleanup_expired_stories failed: {e}")
        return 0
