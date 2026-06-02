from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated
from src.dependencies.database import get_pg_db
from src.dependencies.auth import get_current_user
from src.database.models.user import User
from src.schemas.comment import CommentCreate, CommentUpdate, CommentResponse
from src.repositories import comment_repo
from src.repositories.post_repo import get_post_by_id
from src.core.exceptions import (
    CommentNotFoundError,
    PostNotFoundError,
    UnauthorizedAccessError,
)

router = APIRouter(tags=["Comments"])


@router.post(
    "/post/{post_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    post_id: int,
    data: CommentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_pg_db),
):
    """
    Create a new comment on a post.

    Verifies that the target post exists, then creates a comment
    associated with the authenticated user.

    Args:
        post_id: ID of the post to comment on.
        data: Comment creation payload.
        current_user: Authenticated user.
        db: Database session dependency.

    Returns:
        The created CommentResponse.
    """
    post = await get_post_by_id(db, post_id)

    if not post:
        raise PostNotFoundError("Post not found")

    return await comment_repo.create_comment(
        db,
        user_id=current_user.id,
        post_id=post_id,
        data=data,
    )


@router.get("/post/{post_id}", response_model=list[CommentResponse])
async def get_comments_for_post(
    post_id: int,
    db: AsyncSession = Depends(get_pg_db),
    limit: int = 10,
    skip: int = 0,
):
    """
    Retrieve paginated comments for a post.

    Fetches comments for the given post with pagination support.

    Args:
        post_id: ID of the post.
        db: Database session dependency.
        limit: Maximum number of comments to return.
        skip: Pagination offset.

    Returns:
        List of CommentResponse objects.
    """
    return await comment_repo.get_comments_by_post(
        db,
        post_id=post_id,
        limit=limit,
        skip=skip,
    )


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_pg_db),
):
    """
    Retrieve a comment by its ID.

    Fetches a single comment. Raises an error if not found.

    Args:
        comment_id: ID of the comment.
        db: Database session dependency.

    Returns:
        CommentResponse object.

    Raises:
        CommentNotFoundError: If comment does not exist.
    """

    comment = await comment_repo.get_comment_by_id(db, comment_id)

    if not comment:
        raise CommentNotFoundError()

    return comment


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    data: CommentUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_pg_db),
):
    """
    Update an existing comment.

    Allows only the comment owner to update their comment.

    Args:
        comment_id: ID of the comment to update.
        data: Fields to update.
        current_user: Authenticated user.
        db: Database session dependency.

    Returns:
        Updated CommentResponse.

    Raises:
        CommentNotFoundError: If comment does not exist.
        UnauthorizedAccessError: If user is not the owner.
    """
    comment = await comment_repo.get_comment_by_id(db, comment_id)

    if not comment:
        raise CommentNotFoundError()

    if comment.user_id != current_user.id:
        raise UnauthorizedAccessError("Not allowed to update this comment")

    return await comment_repo.update_comment(
        db,
        comment=comment,
        data=data,
    )


@router.delete("/{comment_id}", status_code=200)
async def delete_comment(
    comment_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_pg_db),
):
    """
    Delete a comment.

    Allows deletion if:
        - User is the comment owner, OR
        - User is the owner of the post containing the comment.

    Args:
        comment_id: ID of the comment.
        current_user: Authenticated user.
        db: Database session dependency.

    Returns:
        None

    Raises:
        CommentNotFoundError: If comment does not exist.
        UnauthorizedAccessError: If user is not allowed to delete it.
    """

    comment = await comment_repo.get_comment_by_id(db, comment_id)

    if not comment:
        raise CommentNotFoundError()
    if not (
        comment.user_id == current_user.id or comment.post.user_id == current_user.id
    ):
        raise UnauthorizedAccessError("Not allowed to delete this comment")

    await comment_repo.delete_comment(db, comment=comment)

    return None


@router.get("/user/{user_id}", response_model=list[CommentResponse])
async def get_comments_by_user(
    user_id: int,
    db: AsyncSession = Depends(get_pg_db),
    limit: int = 10,
    skip: int = 0,
):
    """
    Retrieve comments created by a specific user.

    Returns paginated comments for a given user ID.

    Args:
        user_id: ID of the user.
        db: Database session dependency.
        limit: Maximum number of comments to return.
        skip: Pagination offset.

    Returns:
        List of CommentResponse objects.
    """
    return await comment_repo.get_comments_by_user(
        db,
        user_id=user_id,
        limit=limit,
        skip=skip,
    )
