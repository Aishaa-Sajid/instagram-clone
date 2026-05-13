from src.database.models.user import User
from src.database.models.follow import Follow
from src.services.cloudinary.cloudinary_service import delete_image_from_cloudinary
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, timezone

from src.database.models.story import Story


async def create_story(
    db: AsyncSession,
    *,
    user_id: int,
    media_url: str,
    public_id: str,
) -> Story:
    """
     Create a new story for a user.

    This function creates and stores a new story record in the database
    using the provided media URL and user ID. Story expiration is handled
    dynamically using the `created_at` timestamp instead of storing a
    separate expiration field.

    Args:
        db (AsyncSession): Active database session used for persistence.
        user_id (int): ID of the user creating the story.
        media_url (str): URL of the uploaded story media.

    Returns:
        Story: The newly created story instance.

    """
    try:
        story = Story(
            user_id=user_id,
            media_url=media_url,
            public_id=public_id,
        )

        db.add(story)
        await db.commit()
        await db.refresh(story)

        return story

    except Exception as e:
        await db.rollback()
        raise Exception(f"Failed to create story: {str(e)}")


async def get_active_stories(
    db: AsyncSession,
    *,
    skip: int,
    limit: int,
    viewer_id: int,
) -> list[Story]:
    """
    Retrieve active stories with pagination.

    A story is considered active if it was created within the
    last 24 hours. The function fetches active stories ordered
    by newest first and applies pagination.

    Args:
        db (AsyncSession): Active database session used for querying.
        skip (int): Number of records to skip for pagination.
        limit (int): Maximum number of records to return.
        viewer_id (int): ID of the user viewing the stories.
    Returns:
        list[Story]: List of active story objects with loaded owner data.

    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)

    follow_subq = select(Follow.id).where(
        (Follow.follower_id == viewer_id)
        & (Follow.following_id == Story.user_id)
        & (Follow.status == "accepted")
    )

    stmt = (
        select(Story)
        .join(User, Story.user_id == User.id)
        .options(selectinload(Story.story_owner))
        .where(
            Story.created_at >= cutoff,
            (
                (User.is_private == False) 
                | follow_subq.exists()),
        )
        .order_by(Story.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(stmt)
    return result.scalars().all()


async def delete_expired_stories(db: AsyncSession) -> int:
    """
    Delete expired stories from the database.

    A story is considered expired if it was created more than
    24 hours ago. This function permanently removes expired
    stories from the database.

    Args:
        db (AsyncSession): Active database session used for deletion.

    Returns:
        int: Number of deleted story records.
    """
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        stmt = select(Story).where(Story.created_at <= cutoff)

        result = await db.execute(stmt)
        expired_stories = result.scalars().all()

        deleted_count = 0

        for story in expired_stories:

            await delete_image_from_cloudinary(story.public_id)

            await db.delete(story)

            deleted_count += 1

        await db.commit()

        return deleted_count

    except Exception as e:
        await db.rollback()
        raise Exception(f"Failed to delete expired stories: {str(e)}")
