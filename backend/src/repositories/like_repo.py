from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models.like import Like
from sqlalchemy.orm import selectinload

async def toggle_like(db: AsyncSession, user_id: int, post_id: int) -> bool:
    """
    Toggle like status for a post by a user.

    If a like already exists, it is removed (unlike operation).
    If no like exists, a new like is created.

    Args:
        db: The asynchronous SQLAlchemy database session.
        user_id: ID of the user performing the action.
        post_id: ID of the post being liked or unliked.

    Returns:
        True if the post is liked after the operation,
        False if the post is unliked.
    """
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


async def get_like_count(db: AsyncSession, post_id: int) -> int:
    """
    Get the total number of likes for a specific post.

    Args:
        db: The asynchronous SQLAlchemy database session.
        post_id: ID of the post.

    Returns:
        Total number of likes for the post.
    """

    result = await db.execute(
        select(func.count(Like.id)).where(Like.post_id == post_id)
    )
    return result.scalar() or 0




async def get_post_liked_users(
    db: AsyncSession,
    *,
    post_id: int,
    limit: int,
    skip: int,
) -> list[Like]:
    """
    Retrieve users who liked a specific post (paginated).

    Fetches Like records with associated user data using eager loading
    to avoid N+1 query issues. Results are ordered by newest likes first.

    Args:
        db: The asynchronous SQLAlchemy database session.
        post_id: ID of the post whose likes are being retrieved.
        limit: Maximum number of records to return.
        skip: Number of records to skip (pagination offset).

    Returns:
        List of Like ORM instances with loaded user relationships.
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
