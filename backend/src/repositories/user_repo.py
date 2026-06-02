from datetime import datetime, timezone
from src.core.exceptions import (
    ConflictError,
    ExternalServiceError,
    UserNotFoundError,
    ValidationError,
)
from src.celery.tasks.email_tasks import send_verification_email_task
from src.database.models.follow import Follow
from src.utils.enum import FollowStatus
from sqlalchemy import select, update, func, or_, case
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.cloudinary_service import delete_image_from_cloudinary
from src.utils.password_verification import hash_password, verify_password
from src.schemas.user import UpdatePasswordSchema, UserCreate, UserOut, UserProfileOut
from src.database.models.user import User
import secrets
from loguru import logger


async def get_follow_stats(
    db: AsyncSession,
    *,
    user_id: int,
    current_user_id: int | None,
):
    """
    Retrieve follower statistics for a user.

    Calculates:
        - Total followers (accepted)
        - Total following (accepted)
        - Follow status between current user and target user (if provided)

    Args:
        db: The asynchronous SQLAlchemy database session.
        user_id: ID of the user whose stats are being retrieved.
        current_user_id: ID of the requesting user (optional).

    Returns:
        Tuple containing:
            - followers_count (int)
            - following_count (int)
            - follow_status (FollowStatus | None)
    """
    stmt = select(
        func.count().filter(
            Follow.following_id == user_id,
            Follow.status == FollowStatus.ACCEPTED,
        ),
        func.count().filter(
            Follow.follower_id == user_id,
            Follow.status == FollowStatus.ACCEPTED,
        ),
    )
    
    result = await db.execute(stmt)
    followers_count, following_count = result.one()
    
    follow_status = None

    if current_user_id:
        follow_status = await db.scalar(
            select(Follow.status).where(
                Follow.follower_id == current_user_id,
                Follow.following_id == user_id,
            )
        )

    return (
        followers_count or 0,
        following_count or 0,
        follow_status,
    )


async def get_user_by_id(
    db: AsyncSession, user_id: int, current_user_id: int | None = None
) -> User | None:
    """
    Retrieve a user by ID.

    Only returns non-deleted users.

    Args:
        db: The asynchronous database session.
        user_id: ID of the user to retrieve.
        current_user_id: ID of the requesting user (optional, unused here).

    Returns:
        The User ORM instance.

    Raises:
        UserNotFoundError: If the user does not exist or is deleted.
    """

    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )

    user = result.scalar_one_or_none()
    if not user:
        raise UserNotFoundError("User not found")

    return user

async def get_user_profile(db: AsyncSession, user_id: int, current_user_id: int | None = None) -> UserProfileOut:
    """
    Retrieve a user's profile with follow statistics.

    Combines:
        - User data
        - Follower count
        - Following count
        - Follow relationship status (if viewer provided)

    Args:
        db: The asynchronous database session.
        user_id: ID of the user whose profile is being retrieved.
        current_user_id: ID of the requesting user (optional).

    Returns:
        UserProfileOut containing user data and follow stats.
    """
    user = await get_user_by_id(db, user_id, current_user_id)
    followers_count, following_count, follow_status = await get_follow_stats(db, user_id=user_id, current_user_id=current_user_id)

    return UserProfileOut(
        user=user,
        followers_count=followers_count,
        following_count=following_count,
        follow_status=follow_status,
    )



async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """
    Retrieve a user by email.

    Args:
        db: The asynchronous database session.
        email: Email address to search for.

    Returns:
        User instance if found, otherwise None.
    """
    result = await db.execute(
        select(User).where(User.email == email, User.deleted_at.is_(None))
    )

    return result.scalars().first()


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """
    Create a new user account.

    Steps:
        - Validate email uniqueness
        - Hash password
        - Generate verification token
        - Create user record
        - Send verification email asynchronously

    Args:
        db: The asynchronous database session.
        user: User creation payload.

    Returns:
        The created User instance.

    Raises:
        ConflictError: If email is already registered.
    """
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        raise ConflictError("Email already registered")

    hashed_password = await hash_password(user.password)
    verification_token = secrets.token_urlsafe(32)
    new_user = User(
        **user.model_dump(exclude={"password"}),
        password=hashed_password,
        verification_token=verification_token,
        is_verified=False,
    )
    db.add(new_user)

    await db.commit()

    await db.refresh(new_user)

    try:
        send_verification_email_task.delay(new_user.email, verification_token)
    except Exception:
        logger.exception(f"Failed to queue verification email for user {new_user.id}")

    return new_user


async def update_user(
    db: AsyncSession,
    user: User,
    bio: str | None = None,
    is_private: bool | None = None,
    image_url: str | None = None,
    public_id: str | None = None,
) -> User | None:
    """
    Update user profile fields.

    Updates only the fields that are explicitly provided.

    Args:
        db: The asynchronous database session.
        user: The user instance to update.
        bio: Optional updated bio.
        is_private: Optional privacy setting.
        image_url: Optional profile image URL.
        public_id: Optional Cloudinary public ID.

    Returns:
        The updated User instance.

    Raises:
        UserNotFoundError: If user instance is invalid.
    """
    if not user:
        raise UserNotFoundError()

    if bio is not None:
        user.bio = bio

    if is_private is not None:
        user.is_private = is_private

    if image_url is not None:
        user.profile_picture = image_url

    if public_id is not None:
        user.public_id = public_id

    await db.commit()


    await db.refresh(user)

    return user


async def delete_user_by_id(db: AsyncSession, user_id: int) -> bool:
    """
    Soft delete a user account and remove profile image from Cloudinary.

    Steps:
        - Retrieve user
        - Delete profile image from Cloudinary (if exists)
        - Soft delete user by setting deleted_at timestamp

    Args:
        db: The asynchronous database session.
        user_id: ID of the user to delete.

    Returns:
        True if deletion was successful.

    Raises:
        UserNotFoundError: If user does not exist.
    """

    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalars().first()

    if not user:
        raise UserNotFoundError("User not found")

    stmt = (
        update(User)
        .where(User.id == user_id, User.deleted_at.is_(None))
        .values(deleted_at=datetime.now(timezone.utc))
    )

    await db.execute(stmt)
    await db.commit()
    
    if user.public_id:
        try:
            await delete_image_from_cloudinary(user.public_id)
        except ExternalServiceError:
            logger.exception(f"Failed to delete profile picture from Cloudinary for user {user_id}")

    return True


async def search_users(
    db: AsyncSession,
    query: str,
    limit: int = 20,
    offset: int = 0,
) -> list[User]:
    """
    Search users by username using fuzzy matching.

    Uses PostgreSQL trigram similarity and prefix matching to rank results.

    Ranking priority:
        - Exact match
        - Prefix match
        - Similarity score

    Args:
        db: The asynchronous database session.
        query: Search keyword.
        limit: Maximum number of results.
        offset: Pagination offset.

    Returns:
        List of matching User instances.
    """
    similarity_threshold = 0.3
    score=case(
        (User.username==query,3),
        (User.username.ilike(f"{query}%"),2),
        else_=func.similarity(User.username, query))
    
    stmt = (
        select(User)
        .where(
            User.deleted_at.is_(None),
            or_(
                User.username.ilike(f"{query}%"),
                func.similarity(User.username, query) > similarity_threshold,
            ),
        )
        .order_by(score.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(stmt)
    return result.scalars().all()



async def update_password(
    db: AsyncSession,
    *,
    user: User,
    payload: UpdatePasswordSchema,
):
    """
    Update a user's password after validation.

    Validations:
        - Current password must be correct
        - New password must differ from old password

    Args:
        db: The asynchronous database session.
        user: The user whose password is being updated.
        payload: Password update payload.

    Returns:
        Dict containing success message.

    Raises:
        ValidationError: If password validation fails.
    """

    if not await verify_password(payload.current_password, user.password):
        raise ValidationError("Current password is incorrect")

    if await verify_password(payload.new_password, user.password):
        raise ValidationError("New password cannot be same as old password")

    user.password = await hash_password(payload.new_password)

    await db.commit()


    return {"message": "Password updated successfully"}
