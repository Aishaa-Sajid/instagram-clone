from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated

from src.dependencies.database import get_pg_db
from src.dependencies.auth import get_current_user
from src.database.models.user import User

from src.schemas.comment import CommentCreate, CommentUpdate, CommentResponse
from src.repositories import comment_repo
from src.repositories.post_repo import get_post_by_id

router = APIRouter(tags=["Comments"])


@router.post("/post/{post_id}", response_model=CommentResponse, status_code=201)
async def create_comment(
    post_id: int,
    data: CommentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_pg_db),
):
    """
    Create a new comment on a specific post.

    This endpoint verifies that the target post exists, then creates a new
    comment associated with the authenticated user and the given post.

    Args:
        post_id (int): ID of the post where the comment will be created.
        data (CommentCreate): Request body containing comment content.
        current_user (User): The authenticated user making the request.
        db (AsyncSession): Database session dependency.

    Returns:
        CommentResponse: The newly created comment.

    Raises:
        HTTPException:
            - 404 if the post does not exist
            - 500 if an unexpected database error occurs
    """

    try:
        post = await get_post_by_id(db, post_id)

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        return await comment_repo.create_comment(
            db,
            user_id=current_user.id,
            post_id=post_id,
            data=data,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create comment")


@router.get("/post/{post_id}", response_model=list[CommentResponse])
async def get_comments_for_post(
    post_id: int,
    db: AsyncSession = Depends(get_pg_db),
    limit: int = 10,
    skip: int = 0,
):
    """
    Retrieve paginated comments for a specific post.

    This endpoint fetches all comments associated with a given post ID,
    applying pagination using limit and skip parameters. Comments are
    returned in descending order of creation time (handled in repository).

    Args:
        post_id (int): ID of the post whose comments are being retrieved.
        db (AsyncSession): Database session dependency.
        limit (int): Maximum number of comments to return (default: 10).
        skip (int): Number of comments to skip for pagination (default: 0).

    Returns:
        list[CommentResponse]: List of comments for the specified post.

    Raises:
        HTTPException:
            - 500 if an unexpected database error occurs
    """
    try:
        return await comment_repo.get_comments_by_post(
            db,
            post_id=post_id,
            limit=limit,
            skip=skip,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch comments for post")


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_pg_db),
):
    """
    Retrieve a single comment by its unique ID.

    This endpoint fetches a comment from the database using its ID. If the
    comment does not exist, a 404 error is returned.

    Args:
        comment_id (int): Unique identifier of the comment to retrieve.
        db (AsyncSession): Database session dependency.

    Returns:
        CommentResponse: The requested comment data.
    """
    try:
        comment = await comment_repo.get_comment_by_id(db, comment_id)

        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        return comment

    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve comment")


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    data: CommentUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_pg_db),
):
    """
    Update an existing comment.

    This endpoint allows a user to update their own comment. It first verifies
    that the comment exists, then checks whether the requesting user is the
    owner of the comment. Only authorized users are allowed to update it.

    Args:
        comment_id (int): ID of the comment to update.
        data (CommentUpdate): Payload containing fields to update.
        current_user (User): The authenticated user making the request.
        db (AsyncSession): Database session dependency.

    Returns:
        CommentResponse: The updated comment.
    """
    try:
        comment = await comment_repo.get_comment_by_id(db, comment_id)

        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        if comment.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed")

        return await comment_repo.update_comment(
            db,
            comment=comment,
            data=data,
        )

    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update comment")


@router.delete("/{comment_id}", status_code=200)
async def delete_comment(
    comment_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_pg_db),
):
    """
    Delete a comment from the system.

    This endpoint allows deletion of a comment if the requesting user is
    either:
    - The owner of the comment, or
    - The owner of the post to which the comment belongs.

    It first verifies the existence of the comment, then checks authorization
    before performing the delete operation.

    Args:
        comment_id (int): ID of the comment to be deleted.
        current_user (User): The authenticated user making the request.
        db (AsyncSession): Database session dependency.

    Returns:
        None
    """
    try:
        comment = await comment_repo.get_comment_by_id(db, comment_id)

        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        if not (
            comment.user_id == current_user.id
            or comment.post.user_id == current_user.id
        ):
            raise HTTPException(status_code=403, detail="Not allowed")

        await comment_repo.delete_comment(db, comment=comment)

        return None

    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete comment")


@router.get("/user/{user_id}", response_model=list[CommentResponse])
async def get_comments_by_user(
    user_id: int,
    db: AsyncSession = Depends(get_pg_db),
    limit: int = 10,
    skip: int = 0,
):
    """
    Retrieve paginated comments created by a specific user.

    This endpoint fetches comments authored by a given user ID and applies
    pagination using limit and skip parameters. Comments are typically
    ordered by creation time in descending order (handled in repository layer).

    Args:
        user_id (int): ID of the user whose comments are being retrieved.
        db (AsyncSession): Database session dependency.
        limit (int): Maximum number of comments to return (default: 10).
        skip (int): Number of comments to skip for pagination (default: 0).

    Returns:
        list[CommentResponse]: List of comments created by the user.
    """
    try:
        return await comment_repo.get_comments_by_user(
            db,
            user_id=user_id,
            limit=limit,
            skip=skip,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch user comments")
