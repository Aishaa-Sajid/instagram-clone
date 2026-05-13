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
    Follow a user.

    Creates a follow relationship from the current authenticated user
    to the target user specified by user_id.

    Args:
        user_id (int): ID of the user to follow.
        db (AsyncSession): Database session dependency.
        current_user (User): The authenticated user performing the action.

    Returns:
        FollowOut: The created follow relationship.
    """
    return await follow_repo.follow_user(db, current_user, user_id)


@router.delete("/{user_id}", status_code=204)
async def unfollow_user(
    user_id: int,
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    """
    Unfollow a user.

    Removes an existing follow relationship between the current user
    and the target user.

    Args:
        user_id (int): ID of the user to unfollow.
        db (AsyncSession): Database session dependency.
        current_user (User): The authenticated user performing the action.

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
    Get incoming follow requests.

    Retrieves all pending follow requests received by the current user.

    Args:
        db (AsyncSession): Database session dependency.
        current_user (User): The authenticated user.

    Returns:
        list[FollowResponse]: List of pending follow requests.
    """
    return await follow_repo.get_follow_requests(db, current_user)


@router.get("/followers", response_model=list[FollowResponse])
async def get_followers(
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get followers of the current user.

    Retrieves all users who are following the current authenticated user.

    Args:
        db (AsyncSession): Database session dependency.
        current_user (User): The authenticated user.

    Returns:
        list[FollowResponse]: List of followers.
    """
    return await follow_repo.get_followers(db, current_user)


@router.patch("/{user_id}", response_model=FollowOut)
async def update_follow_status(
    follow_id: int,
    payload: FollowStatusUpdate,
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update follow request status.

    Updates the status of a follow request (e.g., accepted or rejected)
    for a specific target user.

    Args:
        follow_id (int): ID of the follow relationship to update.
        payload (FollowStatusUpdate): New status for the follow request.
        db (AsyncSession): Database session dependency.
        current_user (User): The authenticated user performing the action.

    Returns:
        FollowOut: Updated follow relationship.
    """
    return await follow_repo.update_follow_status(
        db=db,
        current_user=current_user,
        follow_id=follow_id,
        new_status=payload.status,
    )
