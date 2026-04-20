from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src import utils
from src.schemas.user import UserCreate, UserUpdate
from src.database.models.user import User
import secrets
from src.services.email_service import send_verification_email


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """
    Create a new user in the database.

    Args:
        db (AsyncSession): database session
        user (UserCreate): user input schema

    Returns:
        models.User: created user instance
    """
    hashed_password = utils.hash(user.password)
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
        print("EMAIL FAILED:", repr(e))

    return new_user


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """
    Fetch a user by ID.

    Args:
        db (AsyncSession): database session
        user_id (int): user id

    Returns:
        models.User | None
    """

    result = await db.execute(select(User).where(User.id == user_id))

    return result.scalar_one_or_none()


async def update_user(
    db: AsyncSession,
    user_id: int,
    user_data: UserUpdate | None,
    image_url: str | None = None,
) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return None

    if user_data:
        update_data = user_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(user, key, value)

    if image_url:
        user.profile_picture = image_url

    await db.commit()
    await db.refresh(user)

    return user


# async def update_profile_picture(db, user_id: int, image_url: str):
#     result = await db.execute(select(User).where(User.id == user_id))
#     user = result.scalar_one_or_none()

#     user.profile_picture = image_url

#     await db.commit()
#     await db.refresh(user)

#     return user


async def delete_user_by_id(db: AsyncSession, user_id: int) -> bool:
    stmt = delete(User).where(User.id == user_id)

    result = await db.execute(stmt)
    await db.commit()

    # result.rowcount tells how many rows were deleted
    return result.rowcount > 0
