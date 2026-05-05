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
    Create a new comment for a specific post.

    This function persists a new comment in the database, linking it to
    the given user and post. It commits the transaction and refreshes
    the instance before returning it.

    Args:
        db (AsyncSession): The asynchronous SQLAlchemy database session.
        user_id (int): ID of the user creating the comment.
        post_id (int): ID of the post on which the comment is created.
        data (CommentCreate): Pydantic schema containing comment input data.

    Returns:
        Comment: The newly created Comment ORM instance.
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
    Retrieve a comment by its unique ID, including related user and post data.

    This function fetches a single Comment record from the database and
    eagerly loads its associated user and post relationships using
    selectinload to avoid lazy-loading during later access.

    Args:
        db (AsyncSession): The asynchronous SQLAlchemy database session.
        comment_id (int): The unique identifier of the comment to retrieve.

    Returns:
        Comment | None: The Comment ORM instance if found, otherwise None.

    """
    result = await db.execute(
        select(Comment)
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
    Retrieve paginated comments for a specific post, including user data.

    This function fetches comments belonging to a given post, applies
    pagination using limit and offset, and eagerly loads the associated
    user for each comment to avoid N+1 query issues.

    Comments are ordered by creation time in descending order (newest first).

    Args:
        db (AsyncSession): The asynchronous SQLAlchemy database session.
        post_id (int): ID of the post whose comments are being retrieved.
        limit (int): Maximum number of comments to return.
        skip (int): Number of comments to skip (used for pagination).

    Returns:
        Sequence[Comment]: A list of Comment ORM instances matching the query.
    """
    result = await db.execute(
        select(Comment)
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
    Retrieve paginated comments made by a specific user, including post data.

    This function fetches comments authored by a given user, applies
    pagination using limit and offset, and eagerly loads the associated
    post for each comment to avoid N+1 query issues.

    Comments are ordered by creation time in descending order (newest first).

    Args:
        db (AsyncSession): The asynchronous SQLAlchemy database session.
        user_id (int): ID of the user whose comments are being retrieved.
        limit (int): Maximum number of comments to return.
        skip (int): Number of comments to skip (used for pagination).

    Returns:
        Sequence[Comment]: A list of Comment ORM instances belonging to the user.
    """
    result = await db.execute(
        select(Comment)
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
    Update an existing comment's fields.

    This function applies partial updates to a Comment instance using the
    provided update schema. Only fields explicitly set in the request
    payload are updated. After applying changes, the function commits the
    transaction and refreshes the instance before returning it.

    Args:
        db (AsyncSession): The asynchronous SQLAlchemy database session.
        comment (Comment): The existing Comment ORM instance to update.
        data (CommentUpdate): Pydantic schema containing fields to update.

    Returns:
        Comment: The updated Comment ORM instance.
    """
    if data.content is not None:
        comment.content = data.content

    await db.commit()
    await db.refresh(comment)

    return comment


async def delete_comment(
    db: AsyncSession,
    *,
    comment: Comment
) -> None:
    
    """
    Delete an existing comment from the database.

    This function permanently removes the provided Comment instance from
    the database and commits the transaction.

    Args:
        db (AsyncSession): The asynchronous SQLAlchemy database session.
        comment (Comment): The Comment ORM instance to be deleted.

    Returns:
        None
    """
    await db.delete(comment)
    await db.commit()