from datetime import datetime, timezone
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.password_verification import hash
from src.schemas.user import UserCreate, UserOut
from src.database.models.user import User
import secrets
from src.services.email_service import send_verification_email


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """
    Fetch a user by ID.

    Args:
        db (AsyncSession): database session
        user_id (int): user id

    Returns:
        models.User | None
    """

    result = await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))

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
    result = await db.execute(select(User).where(User.email == email, User.deleted_at.is_(None)))

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
    hashed_password = hash(user.password)
    verification_token = secrets.token_urlsafe(32)
    new_user = User(
        **user.model_dump(exclude={"password"}),
        password=hashed_password,
        verification_token=verification_token,
        is_verified=False
    )

    try:
        await send_verification_email(new_user.email, verification_token)
    except Exception as e:
        raise Exception("Failed to send verification email") from e

    db.add(new_user)
    await db.commit()

    await db.refresh(new_user)
    return new_user


async def update_user(
    db: AsyncSession,
    user_id: int,
    bio: str | None = None,
    is_private: bool | None = None,
    image_url: str | None = None,
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

    await db.commit()
    await db.refresh(user)

    return user


async def delete_user_by_id(db: AsyncSession, user_id: int) -> bool:
    """
    Delete a user from the database by their ID.

    Executes a delete operation for the user matching the given ID.
    Commits the transaction and returns whether any row was deleted.

    Args:
        db (AsyncSession): The asynchronous database session.
        user_id (int): The unique identifier of the user to delete.

    Returns:
        bool: True if a user was deleted, False if no matching user was found.

    """
    
    stmt = (
        update(User)
        .where(User.id == user_id, User.deleted_at.is_(None))
        .values(deleted_at=datetime.now(timezone.utc))
    )

    result = await db.execute(stmt)
    await db.commit()

    return result.rowcount > 0
