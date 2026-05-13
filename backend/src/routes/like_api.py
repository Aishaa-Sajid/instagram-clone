from fastapi import APIRouter, Depends, HTTPException
from src.schemas.user import UserPreview
from sqlalchemy.ext.asyncio import AsyncSession
from src.dependencies.database import get_pg_db
from src.dependencies.auth import get_current_user
from src.database.models import User
from src.repositories import like_repo, post_repo
from src.schemas.like import LikeOut, LikeResponse

router = APIRouter(tags=["Likes"])


@router.post("/{post_id}", response_model=LikeResponse)
async def toggle_like(
    post_id: int,
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    """
    Toggle like status for a post by the current user.

    If the user has already liked the post, the like will be removed.
    If the user has not liked the post, a new like will be created.

    Args:
        post_id (int): ID of the post to like/unlike.
        db (AsyncSession): Database session dependency.
        current_user (User): Currently authenticated user.

    Returns:
        LikeResponse: Object containing updated like status and total like count.

    """
    try:
        post = await post_repo.get_post_by_id(db, post_id)

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        liked = await like_repo.toggle_like(db, current_user.id, post_id)
        likes_count = await like_repo.get_like_count(db, post_id)

        return LikeResponse(liked=liked, likes_count=likes_count)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to toggle like on post"
        ) from e


@router.get("/{post_id}/likes", response_model=list[LikeOut])
async def get_likes_by_post(
    post_id: int,
    limit: int = 10,
    skip: int = 0,
    db: AsyncSession = Depends(get_pg_db),
    _: User = Depends(get_current_user),
):
    post = await post_repo.get_post_by_id(db, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    likes = await like_repo.get_post_liked_users(
        db=db,
        post_id=post_id,
        limit=limit,
        skip=skip,
    )

    return likes
