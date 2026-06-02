from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from collections.abc import Sequence
from sqlalchemy.orm import selectinload
from loguru import logger
from src.database.models.comment import Comment
from src.schemas.comment import CommentCreate, CommentUpdate


async def create_comment(
    db: AsyncSession, *, user_id: int, post_id: int, data: CommentCreate
) -> Comment:
    """
    Create a new comment for a specific post.

    Persists a new comment linked to the given user and post,
    commits the transaction, and refreshes the instance before returning.

    Args:
        db: The asynchronous SQLAlchemy database session.
        user_id: ID of the user creating the comment.
        post_id: ID of the post on which the comment is created.
        data: Pydantic schema containing comment input data.

    Returns:
        The newly created Comment ORM instance.
    """

    comment = Comment(
        content=data.content,
        user_id=user_id,
        post_id=post_id,
    )

    db.add(comment)
    await db.commit()

    await db.refresh(comment, attribute_names=["user"])

    return comment


async def get_comment_by_id(db: AsyncSession, comment_id: int) -> Comment:
    """
    Retrieve a comment by its unique ID.

    Fetches a comment along with its related user using eager loading
    to avoid lazy-loading during later access.

    Args:
        db: The asynchronous SQLAlchemy database session.
        comment_id: The unique identifier of the comment.

    Returns:
        The Comment ORM instance if found, otherwise None.
    """
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.user))
        .where(Comment.id == comment_id)
    )
    return result.scalar_one_or_none()


async def get_comments_by_post(
    db: AsyncSession, *, post_id: int, limit: int, skip: int
) -> Sequence[Comment]:
    """
    Retrieve paginated comments for a specific post.

    Fetches comments for a given post with pagination support and
    eagerly loads user data to avoid N+1 queries. Results are ordered
    by creation time in descending order.

    Args:
        db: The asynchronous SQLAlchemy database session.
        post_id: ID of the post whose comments are being retrieved.
        limit: Maximum number of comments to return.
        skip: Number of comments to skip for pagination.

    Returns:
        A sequence of Comment ORM instances.
    """
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.user))
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.desc())
        .limit(limit)
        .offset(skip)
    )
    return result.scalars().all()


async def get_comments_by_user(
    db: AsyncSession, *, user_id: int, limit: int, skip: int
) -> Sequence[Comment]:
    """
    Retrieve paginated comments made by a specific user.

    Fetches comments authored by a given user with pagination support
    and eagerly loads associated post data. Results are ordered by
    creation time in descending order.

    Args:
        db: The asynchronous SQLAlchemy database session.
        user_id: ID of the user whose comments are being retrieved.
        limit: Maximum number of comments to return.
        skip: Number of comments to skip for pagination.

    Returns:
        A sequence of Comment ORM instances.
    """

    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.user))
        .where(Comment.user_id == user_id)
        .order_by(Comment.created_at.desc())
        .limit(limit)
        .offset(skip)
    )
    return result.scalars().all()


async def update_comment(
    db: AsyncSession, *, comment: Comment, data: CommentUpdate
) -> Comment:
    """
    Update an existing comment.

    Applies partial updates to a comment instance. Only explicitly
    provided fields are updated. Commits the transaction and refreshes
    the instance before returning.

    Args:
        db: The asynchronous SQLAlchemy database session.
        comment: The existing Comment ORM instance to update.
        data: Pydantic schema containing fields to update.

    Returns:
        The updated Comment ORM instance.
    """
    if data.content is not None:
        comment.content = data.content

    await db.commit()
    
    await db.refresh(comment, attribute_names=["user"])

    return comment


async def delete_comment(db: AsyncSession, *, comment: Comment) -> None:
    """
    Delete an existing comment.

    Permanently removes the provided Comment instance from the database
    and commits the transaction.

    Args:
        db: The asynchronous SQLAlchemy database session.
        comment: The Comment ORM instance to be deleted.

    Returns:
        None
    """
    await db.delete(comment)

    await db.commit()
    