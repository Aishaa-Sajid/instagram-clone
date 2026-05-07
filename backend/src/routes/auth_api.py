from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models.user import User
from src.dependencies.database import get_pg_db
from src.utils.password_verification import verify
from src.core import security
from src.repositories.user_repo import get_user_by_email
from src.schemas.auth import Token, RefreshTokenRequest, AccessTokenResponse
from src.schemas.user import UserLogin
from sqlalchemy import select
from src.schemas.mail_response import VerifyEmailResponse

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_pg_db),
) -> Token:
    """
    Authenticate a user and return a JWT access token.

    This endpoint verifies the user's email and password. If the credentials
    are valid and the user is verified, a JWT access token is generated and returned.

    Args:
        user_credentials (UserLogin): The request body containing user email and password.
        db (AsyncSession): The asynchronous database session.

    Returns:
        Token: A dictionary containing the access token and token type.

    """

    user = await get_user_by_email(db, user_credentials.email)

    invalid_credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Credentials",
    )
    if not user:
        raise invalid_credentials_exception

    if not verify(user_credentials.password, user.password):
        raise invalid_credentials_exception

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email before logging in",
        )

    access_token = security.create_access_token(data={"user_id": user.id})
    refresh_token = security.create_refresh_token(data={"user_id": user.id})

    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_pg_db)):
    """
    Verify a user's email using a verification token.

    This endpoint validates the provided token, marks the corresponding
    user's email as verified, and removes the verification token from
    the database.

    Args:
        token (str): The email verification token.
        db (AsyncSession): The asynchronous database session.

    Returns:
        dict: A message indicating successful email verification.

    """
    result = await db.execute(select(User).where(User.verification_token == token))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    user.is_verified = True
    user.verification_token = None

    await db.commit()

    return VerifyEmailResponse(message="Email verified successfully")

@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(payload: RefreshTokenRequest):
    """
    Refresh JWT access token using a valid refresh token.

    This endpoint validates the provided refresh token, generates a new
    access token, and returns both the new access token and the same
    refresh token.

    Args:
        payload (RefreshTokenRequest): The request body containing the refresh token.
        db (AsyncSession): The asynchronous database session.

    Returns:
        AccessTokenResponse: A response containing the new access token and token type.

    """
    decoded = security.verify_refresh_token(payload.refresh_token)

    user_id = decoded["user_id"]

    new_access_token = security.create_access_token({
        "user_id": user_id
    })

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }