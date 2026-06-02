from fastapi import APIRouter, Depends, HTTPException, status

# from src.schemas.user import UserPreview
from sqlalchemy.ext.asyncio import AsyncSession
from src.dependencies.database import get_pg_db
from src.dependencies.auth import get_current_user
from src.database.models import User
from src.repositories import like_repo, post_repo
from src.schemas.like import LikeOut, LikeResponse
from src.core.exceptions import PostNotFoundError

router = APIRouter(tags=["Likes"])


@router.post("/{post_id}", response_model=LikeResponse)
async def toggle_like(
    post_id: int,
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    """
    Toggle like status for a post.

    If the user has already liked the post, the like is removed.
    If not, a new like is created. Returns updated like status and count.

    Args:
        post_id: ID of the post to like/unlike.
        db: Database session dependency.
        current_user: Authenticated user.

    Returns:
        LikeResponse containing:
            - liked (bool)
            - likes_count (int)

    Raises:
        PostNotFoundError: If the post does not exist.
    """

    post = await post_repo.get_post_by_id(db, post_id)

    if not post:
        raise PostNotFoundError("Post not found")

    liked = await like_repo.toggle_like(db, current_user.id, post_id)
    likes_count = await like_repo.get_like_count(db, post_id)

    return LikeResponse(liked=liked, likes_count=likes_count)



@router.get("/{post_id}/likes", response_model=list[LikeOut])
async def get_likes_by_post(
    post_id: int,
    limit: int = 10,
    skip: int = 0,
    db: AsyncSession = Depends(get_pg_db),
    _: User = Depends(get_current_user),
):
    """
    Retrieve users who liked a post.

    Returns a paginated list of users who liked the specified post.

    Args:
        post_id: ID of the post.
        limit: Maximum number of records to return.
        skip: Pagination offset.
        db: Database session dependency.
        _: Authenticated user (required for access control).

    Returns:
        List of LikeOut objects.

    Raises:
        PostNotFoundError: If the post does not exist.
    """
    post = await post_repo.get_post_by_id(db, post_id)

    if not post:
        raise PostNotFoundError("Post not found")

    likes = await like_repo.get_post_liked_users(
        db=db,
        post_id=post_id,
        limit=limit,
        skip=skip,
    )

    return likes
