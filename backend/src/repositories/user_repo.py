from datetime import datetime, timezone
from src.celery.tasks.email_tasks import send_verification_email_task
from src.database.models.follow import Follow
from src.utils.enum import FollowStatus
from sqlalchemy import select, update, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.cloudinary_service import delete_image_from_cloudinary
from src.utils.password_verification import hash, verify
from src.schemas.user import UpdatePasswordSchema, UserCreate, UserOut
from src.database.models.user import User
import secrets
# from src.services.email_service import send_verification_email
from loguru import logger


async def get_follow_stats(
    db: AsyncSession,
    *,
    user_id: int,
    current_user_id: int | None,
):
    followers_count = await db.scalar(
        select(func.count(Follow.id)).where(
            Follow.following_id == user_id, Follow.status == FollowStatus.ACCEPTED
        )
    )

    following_count = await db.scalar(
        select(func.count(Follow.id)).where(
            Follow.follower_id == user_id, Follow.status == FollowStatus.ACCEPTED
        )
    )

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
    Fetch a user by ID.

    Args:
        db (AsyncSession): database session
        user_id (int): user id

    Returns:
        models.User | None
    """

    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )

    user = result.scalar_one_or_none()
    if not user:
        return None
    followers_count, following_count, follow_status = await get_follow_stats(
        db=db,
        user_id=user_id,
        current_user_id=current_user_id,
    )

    user.followers_count = followers_count
    user.following_count = following_count
    user.follow_status = follow_status
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """
    Fetch user by email from database.

    Args:
        db (AsyncSession): database session
        email (str): user email

    Returns:
        User | None
    """
    result = await db.execute(
        select(User).where(User.email == email, User.deleted_at.is_(None))
    )

    return result.scalars().first()


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """
    Create a new user in the database.

    Args:
        db (AsyncSession): database session
        user (UserCreate): user input schema

    Returns:
        models.User: created user instance
    """
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        raise Exception("Email already registered")

    hashed_password = hash(user.password)
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
    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        raise Exception("Failed to send verification email")

    return new_user


async def update_user(
    db: AsyncSession,
    user: User,
    bio: str | None = None,
    is_private: bool | None = None,
    image_url: str | None = None,
    public_id: str | None = None,
) -> UserOut | None:
    """
    Update a user's details in the database.

    Retrieves a user by ID and updates the provided fields. Only fields
    explicitly set in `user_data` are updated. Optionally updates the
    user's profile picture if `image_url` is provided.

    Args:
        db (AsyncSession): The asynchronous database session.
        user_id (int): The unique identifier of the user to update.
        user_data (UserUpdate | None): Pydantic schema containing fields
            to update. Only non-unset fields will be applied.
        image_url (str | None, optional): URL of the user's profile picture.
            Defaults to None.

    Returns:
        User | None: The updated user object if found, otherwise None.

    """
    if not user:
        return None

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
    Soft delete a user and remove their profile picture from Cloudinary.

    This function performs a soft delete by setting the `deleted_at` field
    for the user with the given ID. Before marking the user as deleted, it
    fetches the user record to retrieve and delete the profile picture from
    Cloudinary (if it exists).

    Steps:
        1. Fetch user by ID if not already deleted.
        2. Delete profile picture from Cloudinary (if available).
        3. Perform a soft delete by updating `deleted_at`.
        4. Commit the transaction.

    Args:
        db (AsyncSession): The asynchronous database session.
        user_id (int): The unique identifier of the user to delete.

    Returns:
        bool: True if the user was found and deleted, False otherwise.
    """

    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalars().first()

    if not user:
        return False

    if user.public_id:
        try:
            await delete_image_from_cloudinary(user.public_id)
        except Exception as e:
            logger.error(e)

    stmt = (
        update(User)
        .where(User.id == user_id, User.deleted_at.is_(None))
        .values(deleted_at=datetime.now(timezone.utc))
    )

    await db.execute(stmt)
    await db.commit()

    return True


async def search_users(
    db: AsyncSession,
    query: str,
    limit: int = 20,
    offset: int = 0,
) -> list[User]:
    """
    Search users by username using PostgreSQL trigram similarity.

    This function performs a fuzzy search on usernames using trigram
    similarity and prefix matching. Results are ranked by similarity score.

    Args:
        db (AsyncSession): Asynchronous database session.
        query (str): Search query string entered by user.
        limit (int, optional): Maximum number of results to return. Defaults to 20.
        offset (int, optional): Number of records to skip for pagination. Defaults to 0.

    Returns:
        list[User]: List of matching users.

    Raises:
        Exception: If database query execution fails.
    """
    try:
        similarity_threshold = 0.3

        stmt = (
            select(User)
            .where(
                User.deleted_at.is_(None),
                or_(
                    User.username.ilike(f"{query}%"),
                    func.similarity(User.username, query) > similarity_threshold,
                ),
            )
            .order_by(func.similarity(User.username, query).desc())
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    except Exception as e:
        logger.error(f"Error in search_users: {e}")
        raise Exception("Failed to search users")


async def update_password(
    db: AsyncSession,
    *,
    user: User,
    payload: UpdatePasswordSchema,
):
    """
    Update the password for an existing user after validating the current password.

    This function performs two main validations before updating the password:
    1. Ensures that the provided current password matches the user's existing password.
    2. Ensures that the new password is not the same as the current password.

    If both validations pass, the user's password is hashed and updated in the database.

    Args:
        db (AsyncSession): The SQLAlchemy asynchronous database session.
        user (User): The user object whose password is being updated.
        payload (UpdatePasswordSchema): Schema containing current_password and new_password.

    Raises:
        Exception: If the current password is incorrect.
        Exception: If the new password is the same as the existing password.

    """

    if not verify(payload.current_password, user.password):
        raise Exception("Current password is incorrect")

    if verify(payload.new_password, user.password):
        raise Exception("New password cannot be same as old password")

    user.password = hash(payload.new_password)

    await db.commit()

    return {"message": "Password updated successfully"}
