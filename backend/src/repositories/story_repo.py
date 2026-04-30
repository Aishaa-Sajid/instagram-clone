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
    Create a new story with a 24-hour expiration.

    Args:
        db (AsyncSession): Database session.
        user_id (int): ID of the story owner.
        media_url (str): Uploaded media URL.

    Returns:
        Story: Created story object.
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
    Retrieve only active (non-expired) stories.

    Args:
        db (AsyncSession): Database session.
        skip (int): Pagination offset.
        limit (int): Number of records.

    Returns:
        list[Story]: Active stories list.
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