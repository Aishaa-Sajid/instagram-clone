from src.utils.enum import FollowStatus
from src.database.models.user import User
from src.database.models.follow import Follow
from src.services.cloudinary_service import delete_image_from_cloudinary
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,delete
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, timezone
from src.database.models.story import Story
from loguru import logger


async def create_story(
    db: AsyncSession,
    *,
    user_id: int,
    media_url: str,
    public_id: str,
) -> Story:
    """
    Create a new story for a user.

    Inserts a new story record into the database using the provided
    media URL and user ID. Story expiration is handled via the
    `created_at` timestamp (24-hour lifecycle rule).

    Args:
        db: The asynchronous database session.
        user_id: ID of the user creating the story.
        media_url: URL of the uploaded story media.
        public_id: Cloudinary public identifier for the media.

    Returns:
        The newly created Story instance.
    """
    story = Story(
        user_id=user_id,
        media_url=media_url,
        public_id=public_id,
    )

    db.add(story)
    await db.commit()

    await db.refresh(story)

    return story


async def get_active_stories(
    db: AsyncSession,
    *,
    skip: int,
    limit: int,
    viewer_id: int,
) -> list[Story]:
    """
    Retrieve active stories visible to a user.

    A story is considered active if it was created within the last 24 hours.
    Visibility is controlled using privacy rules:
        - Public users' stories are visible to everyone.
        - Private users' stories are visible only to accepted followers.

    Supports pagination and returns newest stories first.

    Args:
        db: The asynchronous database session.
        skip: Number of records to skip (pagination).
        limit: Maximum number of records to return.
        viewer_id: ID of the user requesting stories.

    Returns:
        List of Story ORM instances with owner relationship loaded.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)

    follow_subq = select(Follow.id).where(
        (Follow.follower_id == viewer_id)
        & (Follow.following_id == Story.user_id)
        & (Follow.status == FollowStatus.ACCEPTED)
    )

    stmt = (
        select(Story)
        .join(User, Story.user_id == User.id)
        .options(selectinload(Story.story_owner))
        .where(
            Story.created_at >= cutoff,
            ((User.is_private == False) | follow_subq.exists()),
        )
        .order_by(Story.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(stmt)
    return result.scalars().all()


async def delete_expired_stories(db: AsyncSession) -> int:
    """
    Delete expired stories older than 24 hours.

    Finds all stories older than 24 hours, deletes them from the
    database, and removes associated media from Cloudinary.

    Args:
        db: The asynchronous database session.

    Returns:
        Number of deleted story records.
    """

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    stmt = select(Story.id,Story.public_id).where(Story.created_at <= cutoff)

    result = await db.execute(stmt)
    expired_stories = result.all()

    deleted_count = 0
    if not expired_stories:
        return 0
    story_ids = [story_id for story_id, _ in expired_stories]

    await db.execute(
        delete(Story).where(Story.id.in_(story_ids))
    )
    deleted_count = len(story_ids)
    await db.commit()

    for _, public_id in expired_stories:
        if public_id:
            try:
                await delete_image_from_cloudinary(public_id)
            except Exception:
                logger.exception(
                    f"Failed to delete Cloudinary image: {public_id}"
                )

    return deleted_count
