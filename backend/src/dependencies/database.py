from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from src.database.config import sessionmanager


async def get_pg_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency to provide a DB session."""
    logger.debug("Acquiring DB session via dependency")
    async with sessionmanager.session() as session:
        yield session
    logger.debug("DB session released via dependency")
