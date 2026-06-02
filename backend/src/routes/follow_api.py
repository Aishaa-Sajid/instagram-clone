from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.dependencies.database import get_pg_db
from src.dependencies.auth import get_current_user
from src.database.models.user import User
from src.repositories import follow_repo
from src.schemas.follow import FollowOut, FollowResponse, FollowStatusUpdate

router = APIRouter(tags=["Follow"])


@router.post("/{user_id}", response_model=FollowOut)
async def follow_user(
    user_id: int,
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a follow relationship with a user.

    Creates a follow request or direct follow depending on the target
    user's privacy settings.

    Args:
        user_id: ID of the user to follow.
        db: Database session dependency.
        current_user: Authenticated user performing the action.

    Returns:
        The created Follow relationship.
    """
    return await follow_repo.follow_user(db, current_user, user_id)


@router.delete("/{user_id}", status_code=204)
async def unfollow_user(
    user_id: int,
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove a follow relationship.

    Deletes the follow relationship between the current user and target user.

    Args:
        user_id: ID of the user to unfollow.
        db: Database session dependency.
        current_user: Authenticated user performing the action.

    Returns:
        None
    """
    return await follow_repo.unfollow_user(db, current_user, user_id)


@router.get("/requests", response_model=list[FollowResponse])
async def get_follow_requests(
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve incoming follow requests.

    Returns all pending follow requests received by the current user.

    Args:
        db: Database session dependency.
        current_user: Authenticated user.

    Returns:
        List of FollowResponse objects.
    """
    return await follow_repo.get_follow_requests(db, current_user)


@router.get("/followers", response_model=list[FollowResponse])
async def get_followers(
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve followers of the current user.

    Returns all users who are following the authenticated user.

    Args:
        db: Database session dependency.
        current_user: Authenticated user.

    Returns:
        List of FollowResponse objects.
    """
    return await follow_repo.get_followers(db, current_user)


@router.patch("/{follow_id}", response_model=FollowOut)
async def update_follow_status(
    follow_id: int,
    payload: FollowStatusUpdate,
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update the status of a follow request.

    Allows updating a follow request status (e.g., accept or reject)
    for a specific follow relationship.

    Args:
        follow_id: ID of the follow relationship.
        payload: New follow status.
        db: Database session dependency.
        current_user: Authenticated user performing the action.

    Returns:
        Updated Follow relationship.
    """
    return await follow_repo.update_follow_status(
        db=db,
        current_user=current_user,
        follow_id=follow_id,
        new_status=payload.status,
    )
