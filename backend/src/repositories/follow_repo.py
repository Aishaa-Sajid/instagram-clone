from src.core.exceptions import (
    AlreadyFollowingError,
    CannotFollowYourselfError,
    FollowRequestNotFoundError,
    ValidationError,
    PermissionDeniedError,
)
from src.utils.constants import FOLLOW_TRANSITIONS
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models.follow import Follow
from src.database.models.user import User
from src.repositories.user_repo import get_user_by_id
from src.utils.enum import FollowStatus
from loguru import logger
from sqlalchemy.orm import selectinload


async def follow_user(
    db: AsyncSession, current_user: User, target_user_id: int
) -> Follow:
    """
    Create a follow relationship between two users.

    Behavior:
        - If the target user is private, creates a PENDING follow request.
        - If the target user is public, creates an ACCEPTED follow.
        - If a REJECTED follow exists, it is deleted and recreated.
        - Prevents duplicate follow relationships.

    Args:
        db: The asynchronous SQLAlchemy database session.
        current_user: The user initiating the follow.
        target_user_id: The ID of the user being followed.

    Returns:
        The created Follow relationship.

    Raises:
        CannotFollowYourselfError: If a user tries to follow themselves.
        AlreadyFollowingError: If a follow relationship already exists.
    """
    if current_user.id == target_user_id:
        raise CannotFollowYourselfError()

    target_user = await get_user_by_id(db, target_user_id)

    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user.id, Follow.following_id == target_user_id
        )
    )
    existing = result.scalar_one_or_none()

    if existing and existing.status == FollowStatus.REJECTED:
        await db.delete(existing)

        await db.commit()

        return existing

    if existing:
        raise AlreadyFollowingError()

    status = (
        FollowStatus.ACCEPTED if not target_user.is_private else FollowStatus.PENDING
    )

    follow = Follow(
        follower_id=current_user.id, following_id=target_user_id, status=status
    )

    db.add(follow)
    
    await db.commit()
    await db.refresh(follow)

    return follow


async def unfollow_user(db: AsyncSession, current_user: User, target_user_id: int):
    """
    Remove an existing follow relationship.

    This permanently deletes the follow record. A new follow request
    will create a fresh row.

    Args:
        db: The asynchronous SQLAlchemy database session.
        current_user: The user performing the unfollow action.
        target_user_id: The ID of the user being unfollowed.

    Returns:
        None

    Raises:
        FollowRequestNotFoundError: If no follow relationship exists.
    """
    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user.id, Follow.following_id == target_user_id
        )
    )

    follow = result.scalar_one_or_none()

    if not follow:
        logger.warning(f"Unfollow failed: user {current_user.id} -> {target_user_id}")
        raise FollowRequestNotFoundError()
    await db.delete(follow)

    await db.commit()
    logger.info(f"User {current_user.id} unfollowed {target_user_id}")
    

async def get_follow_requests(db: AsyncSession, current_user: User):
    """
    Retrieve pending follow requests for the current user.

    Uses eager loading for `Follow.follower` to ensure safe Pydantic
    serialization with `from_attributes=True`.

    Args:
        db: The asynchronous SQLAlchemy database session.
        current_user: The authenticated user.

    Returns:
        List of pending Follow requests.
    """
    result = await db.execute(
        select(Follow)
        .options(
            selectinload(Follow.follower),
        )
        .where(
            Follow.following_id == current_user.id,
            Follow.status == FollowStatus.PENDING,
        )
    )

    return result.scalars().all()


async def get_followers(db: AsyncSession, current_user: User):
    """
    Retrieve accepted followers of the current user.

    Uses eager loading to safely serialize follower relationships
    in Pydantic response models.

    Args:
        db: The asynchronous SQLAlchemy database session.
        current_user: The authenticated user.

    Returns:
        List of accepted Follow relationships.
    """
    result = await db.execute(
        select(Follow)
        .options(
            selectinload(Follow.follower),
        )
        .where(
            Follow.following_id == current_user.id,
            Follow.status == FollowStatus.ACCEPTED,
        )
    )

    return result.scalars().all()


async def update_follow_status(
    db: AsyncSession,
    current_user: User,
    follow_id: int,
    new_status: FollowStatus,
):
    """
    Update the status of a follow request.

    Enforces allowed state transitions defined in FOLLOW_TRANSITIONS.

    Allowed transitions:
        PENDING → ACCEPTED | REJECTED

    Args:
        db: The asynchronous SQLAlchemy database session.
        current_user: The user performing the update.
        follow_id: The ID of the follow relationship.
        new_status: The desired new follow status.

    Returns:
        The updated Follow relationship.

    Raises:
        FollowRequestNotFoundError: If follow record does not exist.
        PermissionDeniedError: If user is not the recipient of request.
        ValidationError: If transition is not allowed.
    """

    result = await db.execute(
        select(Follow).where(
            Follow.id == follow_id,
        )
    )

    follow = result.scalar_one_or_none()

    if not follow:
        raise FollowRequestNotFoundError()

    if follow.following_id != current_user.id:
        raise PermissionDeniedError("You are not allowed to update this follow request")
    if follow.status == new_status:
        return follow

    allowed = FOLLOW_TRANSITIONS[follow.status]

    if new_status not in allowed:
        raise ValidationError()
    follow.status = new_status
    
    await db.commit()
    
    await db.refresh(follow)

    return follow
