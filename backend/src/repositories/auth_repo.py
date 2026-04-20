from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.models.user import User


async def get_user_by_id(db: AsyncSession, user_id: int):
    """
    Fetch user by ID from database.

    Args:
        db (AsyncSession): database session
        user_id (int): user id

    Returns:
        User | None
    """
    result = await db.execute(select(User).where(User.id == user_id))

    return result.scalars().first()

#  print("abc")  
async def get_user_by_email(db: AsyncSession, email: str):
    """
    Fetch user by email from database.

    Args:
        db (AsyncSession): database session
        email (str): user email

    Returns:
        User | None
    """
    result = await db.execute(select(User).where(User.email == email))

    return result.scalars().first()
