import contextlib
from typing import Any
from collections.abc import AsyncIterator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from loguru import logger
from sqlalchemy.engine import make_url
from src.core.settings import PostgresDatabaseSettings


settings = PostgresDatabaseSettings()
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL


# --------------------------
# Base class for models
# --------------------------
class Base(DeclarativeBase):
    __mapper_args__ = {"eager_defaults": True}


# --------------------------
# Database Session Manager
# --------------------------
class DatabaseSessionManager:
    """Manages SQLAlchemy async engine, sessions, and connections."""

    def __init__(self, url: str, engine_kwargs: dict[str, Any] = {}):
        logger.info("Initializing DatabaseSessionManager...")
        self._engine = create_async_engine(url, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(
            autocommit=False,
            expire_on_commit=False,
            bind=self._engine,
        )
        logger.info("DatabaseSessionManager initialized successfully")

    async def close(self):
        """Close engine and release resources."""
        if self._engine is None:
            logger.error(
                "Attempted to close but DatabaseSessionManager is not initialized"
            )
            raise Exception("DatabaseSessionManager is not initialized")

        logger.info("Disposing SQLAlchemy engine...")
        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None
        logger.info("DatabaseSessionManager closed successfully")

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        """Provide an async database connection."""
        if self._engine is None:
            logger.error(
                "Attempted to connect but DatabaseSessionManager is not initialized"
            )
            raise Exception("DatabaseSessionManager is not initialized")

        logger.debug("Opening async database connection...")
        async with self._engine.begin() as connection:
            try:
                logger.debug("Database connection established")
                yield connection
            except Exception as e:
                logger.exception(f"Error during connection: {e}")
                await connection.rollback()
                raise
            finally:
                logger.debug("Database connection closed")

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Provide an async database session."""
        if self._sessionmaker is None:
            logger.error(
                "Attempted to create session but DatabaseSessionManager is not initialized"
            )
            raise Exception("DatabaseSessionManager is not initialized")

        logger.debug("Creating new database session...")
        session = self._sessionmaker()
        try:
            yield session
            logger.debug("Session completed successfully")
        except Exception as e:
            logger.exception(f"Error during session: {e}. Rolling back...")
            await session.rollback()
            raise
        finally:
            await session.close()
            logger.debug("Session closed")


# --------------------------
# Initialize session manager
# --------------------------
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
safe_db_url = make_url(SQLALCHEMY_DATABASE_URL).render_as_string(
    hide_password=True
)

sessionmanager = DatabaseSessionManager(
    SQLALCHEMY_DATABASE_URL,
    {"echo": settings.echo_sql, "pool_pre_ping": True},
)
