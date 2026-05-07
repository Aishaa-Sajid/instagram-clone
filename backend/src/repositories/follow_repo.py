from sqlalchemy import select
from fastapi import HTTPException, logger
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models.follow import Follow
from src.database.models.user import User
from src.repositories.user_repo import get_user_by_id
from src.utils.enum import FollowStatus


async def follow_user(
    db: AsyncSession, current_user: User, target_user_id: int
) -> Follow:

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

    if existing:
        if existing.status == FollowStatus.REJECTED:
            existing.status = (
                FollowStatus.ACCEPTED
                if not target_user.is_private
                else FollowStatus.PENDING
            )
            await db.commit()
            await db.refresh(existing)
            return existing

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
    result = await db.execute(
        select(Follow).where(
            Follow.following_id == current_user.id,
            Follow.status == FollowStatus.PENDING,
        )
    )

    return result.scalars().all()


async def accept_follow_request(db: AsyncSession, current_user: User, follower_id: int):
    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == follower_id,
            Follow.following_id == current_user.id,
            Follow.status == FollowStatus.PENDING,
        )
    )

    follow = result.scalar_one_or_none()

    if not follow:
        raise Exception("Follow request not found")

    follow.status = FollowStatus.ACCEPTED
    await db.commit()
    await db.refresh(follow)

    return follow


async def reject_follow_request(db: AsyncSession, current_user: User, follower_id: int):
    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == follower_id,
            Follow.following_id == current_user.id,
            Follow.status == FollowStatus.PENDING,
        )
    )

    follow = result.scalar_one_or_none()

    if not follow:
        raise Exception("Follow request not found")

    follow.status = FollowStatus.REJECTED
    await db.commit()
    await db.refresh(follow)

    return follow
