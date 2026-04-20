from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models.user import User
from src.database.dependency import get_pg_db
from src import utils
from src.core import security
from src.repositories.auth_repo import get_user_by_email
from src.schemas.auth import Token
from src.schemas.user import UserLogin
from sqlalchemy import select

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_pg_db),
):
    """
    Authenticate user and return JWT token.
    """

    user = await get_user_by_email(db, user_credentials.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Credentials",
        )

    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Credentials",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email first"
    )
    access_token = security.create_access_token(data={"user_id": user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
#  print("abc") 
@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_pg_db)):

    result = await db.execute(
        select(User).where(User.verification_token == token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    user.is_verified = True
    user.verification_token = None

    await db.commit()

    return {"message": "Email verified successfully"}