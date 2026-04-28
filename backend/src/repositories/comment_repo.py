from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from collections.abc import Sequence

from src.database.models.comment import Comment
from src.schemas.comment import CommentCreate, CommentUpdate


async def create_comment(
    db: AsyncSession,
    *,
    user_id: int,
    post_id: int,
    data: CommentCreate
) -> Comment:
    """
    Create a new comment.

    Args:
        db: database session
        user_id: ID of the user creating comment
        post_id: ID of the post
        data: comment payload

    Returns:
        Comment instance
    """
    comment = Comment(
        content=data.content,
        user_id=user_id,
        post_id=post_id,
    )

    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return comment


async def get_comment_by_id(
    db: AsyncSession,
    comment_id: int
) -> Comment | None:
    """
    Get comment by ID with user + post loaded.
    """
    result = await db.execute(
        select(Comment)
        .options(
            selectinload(Comment.user),
            selectinload(Comment.post),
        )
        .where(Comment.id == comment_id)
    )
    return result.scalar_one_or_none()


async def get_comments_by_post(
    db: AsyncSession,
    *,
    post_id: int,
    limit: int,
    skip: int
) -> Sequence[Comment]:
    """
    Get comments for a post with pagination.
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
    db: AsyncSession,
    *,
    user_id: int,
    limit: int,
    skip: int
) -> Sequence[Comment]:
    """
    Get comments by a specific user.
    """
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.post))
        .where(Comment.user_id == user_id)
        .order_by(Comment.created_at.desc())
        .limit(limit)
        .offset(skip)
    )
    return result.scalars().all()


async def update_comment(
    db: AsyncSession,
    *,
    comment: Comment,
    data: CommentUpdate
) -> Comment:
    """
    Update comment content.
    """
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if hasattr(comment, key):
            setattr(comment, key, value)

    await db.commit()
    await db.refresh(comment)

    return comment


async def delete_comment(
    db: AsyncSession,
    *,
    comment: Comment
) -> None:
    """
    Delete a comment.
    """
    await db.delete(comment)
    await db.commit()