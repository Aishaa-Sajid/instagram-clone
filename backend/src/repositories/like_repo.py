from src.database.models.user import User
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models.like import Like
from sqlalchemy.orm import selectinload


async def toggle_like(db: AsyncSession, user_id: int, post_id: int) -> bool:
    """
    Toggle like status for a given user and post.

    If a like already exists, it will be removed (unlike).
    If no like exists, a new like will be created.

    Args:
        db (AsyncSession): Database session.
        user_id (int): ID of the user performing the action.
        post_id (int): ID of the post to like/unlike.

    Returns:
        bool: True if the post is liked after operation, False if unliked.
    """
    try:
        result = await db.execute(
            select(Like).where(Like.user_id == user_id, Like.post_id == post_id)
        )
        like = result.scalar_one_or_none()

        if like:
            await db.delete(like)
            await db.commit()
            return False

        new_like = Like(user_id=user_id, post_id=post_id)
        db.add(new_like)
        await db.commit()
        return True

    except Exception as e:
        await db.rollback()
        raise Exception("Failed to toggle like") from e


async def get_like_count(db: AsyncSession, post_id: int) -> int:
    """
    Get total number of likes for a specific post.

    Args:
        db (AsyncSession): Database session.
        post_id (int): ID of the post.

    Returns:
        int: Total number of likes for the post.
    """
    try:
        result = await db.execute(
            select(func.count(Like.id)).where(Like.post_id == post_id)
        )
        return result.scalar()

    except Exception as e:
        raise Exception("Failed to fetch like count") from e


async def get_post_liked_users(
    db: AsyncSession,
    *,
    post_id: int,
    limit: int,
    skip: int,
) -> list[Like]:
    """
    Fetch users who liked a specific post (paginated).
    """

    stmt = (
        select(Like)
        .options(selectinload(Like.user))
        .where(Like.post_id == post_id)
        .order_by(Like.created_at.desc())
        .limit(limit)
        .offset(skip)
    )
    
    result = await db.execute(stmt)
    return result.scalars().all()
