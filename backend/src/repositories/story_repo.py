from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta,timezone

from src.database.models.story import Story


async def create_story(
    db: AsyncSession,
    *,
    user_id: int,
    media_url: str,
) -> Story:
    """
     Create a new story with a time-based expiration.

    This function creates a story record for a user, assigns an expiration
    time (currently set to 5 minutes for testing or development purposes),
    persists it to the database, and returns the fully loaded story object
    including its owner relationship.

    Args:
        db (AsyncSession): Database session used for persistence operations.
        user_id (int): ID of the user who owns the story.
        media_url (str): URL of the uploaded media file.

    Returns:
        Story: The created story instance with loaded relationships.

    """
    try:
        # expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)


        story = Story(
            user_id=user_id,
            media_url=media_url,
            expires_at=expires_at,
        )

        db.add(story)
        await db.commit()
        await db.refresh(story)

        result = await db.execute(
            select(Story)
            .options(selectinload(Story.story_owner))
            .where(Story.id == story.id)
        )

        return result.scalar_one()

    except Exception as e:
        await db.rollback()
        raise Exception(f"Failed to create story: {str(e)}")


async def get_active_stories(
    db: AsyncSession,
    *,
    skip: int,
    limit: int,
) -> list[Story]:
    """
    Retrieve active (non-expired) stories with pagination.

    This function fetches stories whose expiration time has not passed,
    orders them by most recently created, and applies pagination using
    skip and limit values.

    Args:
        db (AsyncSession): Database session used for querying.
        skip (int): Number of records to skip (pagination offset).
        limit (int): Maximum number of stories to return.

    Returns:
        list[Story]: List of active (non-expired) story objects.
        
    """
    now = datetime.now(timezone.utc)

    stmt = (
        select(Story)
        .options(selectinload(Story.story_owner))
        .where(Story.expires_at > now)
        .order_by(Story.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(stmt)
    return result.scalars().all()


# async def delete_expired_stories(db: AsyncSession) -> int:
#     """
#     Delete expired stories from database.

#     Returns:
#         int: Number of deleted records.
#     """
#     now = datetime.now(timezone.utc)

#     stmt = delete(Story).where(Story.expires_at <= now)

#     result = await db.execute(stmt)
#     await db.commit()

#     return result.rowcount