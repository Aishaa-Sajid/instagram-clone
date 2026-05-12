from src.utils.constants import FOLLOW_TRANSITIONS
from sqlalchemy import select
from fastapi import HTTPException, logger
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
        - If target user is private → creates PENDING request
        - If target user is public → creates ACCEPTED follow
        - Does NOT handle re-follow logic (handled via delete + re-create)

    Args:
        db (AsyncSession): Database session.
        current_user (User): The user who is following.
        target_user_id (int): The user being followed.

    Returns:
        Follow: Created follow relationship.
    """
    if current_user.id == target_user_id:
        raise Exception("You cannot follow yourself")

    target_user = await get_user_by_id(db, target_user_id)
    if not target_user:
        raise Exception("User not found")

    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user.id, Follow.following_id == target_user_id
        )
    )
    existing = result.scalar_one_or_none()

    if existing and existing.status == FollowStatus.REJECTED:
        await db.delete(existing)
        await db.commit()
        await db.refresh(existing)
        return existing

    if existing:
        raise Exception("Follow already exists")

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

    Behavior:
        - Completely deletes the relationship row
        - Used for both unfollow and reset cases
        - Re-follow will create a new row

    Args:
        db (AsyncSession): Database session.
        current_user (User): The user performing unfollow.
        target_user_id (int): The user being unfollowed.
    """
    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user.id, Follow.following_id == target_user_id
        )
    )

    follow = result.scalar_one_or_none()

    if not follow:
        logger.warning(f"Unfollow failed: user {current_user.id} -> {target_user_id}")
        raise Exception("Follow relationship not found")

    await db.delete(follow)
    await db.commit()
    logger.info(f"User {current_user.id} unfollowed {target_user_id}")


async def get_follow_requests(db: AsyncSession, current_user: User):
    """
    Get pending follow requests for current user.

    Args:
        db (AsyncSession): Database session.
        current_user (User): The logged-in user.

    Returns:
        List[Follow]: List of pending follow requests.
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
    Get accepted followers of the current user.

    Args:
        db (AsyncSession): Database session.
        current_user (User): The logged-in user.

    Returns:
        List[Follow]: List of accepted followers.
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
    target_user_id: int,
    new_status: FollowStatus,
):
    """
    Update follow relationship status using transition rules.

    This function enforces the state machine defined in FOLLOW_TRANSITIONS.

    Allowed transitions:
        PENDING  → ACCEPTED, REJECTED
        ACCEPTED → (none)
        REJECTED → (none) (handled via re-follow = new row)

    Args:
        db (AsyncSession): Database session.
        current_user (User): User performing the action.
        target_user_id (int): User who sent the follow request.
        new_status (FollowStatus): Desired new status.

    Returns:
        Follow: Updated follow relationship.
    """

    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == target_user_id,
            Follow.following_id == current_user.id,
        )
    )

    follow = result.scalar_one_or_none()

    if not follow:
        raise Exception("Follow request not found")

    if follow.status == new_status:
        return follow

    allowed = FOLLOW_TRANSITIONS[follow.status]

    if new_status not in allowed:
        raise Exception(f"Invalid transition: {follow.status} → {new_status}")
    follow.status = new_status

    await db.commit()
    await db.refresh(follow)

    return follow
