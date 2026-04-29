from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.cloudinary.cloudinary_service import delete_image_from_cloudinary
from src.utils.password_verification import hash
from src.schemas.user import UserCreate, UserOut
from src.database.models.user import User
import secrets
from src.services.email_service import send_verification_email

# from src.services.mail.mail_service import send_verification_email
from loguru import logger


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
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

    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str):
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
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash(user.password)
    verification_token = secrets.token_urlsafe(32)
    new_user = User(
        **user.model_dump(exclude={"password"}),
        password=hashed_password,
        verification_token=verification_token,
        is_verified=False
    )
    db.add(new_user)
    await db.commit()

    await db.refresh(new_user)

    try:
        await send_verification_email(new_user.email, verification_token)
    except Exception as e:
        raise Exception("Failed to send verification email") from e

    return new_user


async def update_user(
    db: AsyncSession,
    user_id: int,
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

    user = await get_user_by_id(db, user_id)

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
