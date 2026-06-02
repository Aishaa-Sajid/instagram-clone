from fastapi import APIRouter, Depends
from src.core.exceptions import InvalidCredentialsError, VerificationTokenNotFoundError, UnauthorizedAccessError
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models.user import User
from src.dependencies.database import get_pg_db
from src.utils.password_verification import verify_password
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
    Authenticate a user and return JWT tokens.

    Validates user credentials and ensures the account is verified.
    On success, generates both access and refresh tokens.

    Args:
        user_credentials: Login payload containing email and password.
        db: The asynchronous database session.

    Returns:
        Token containing access token, refresh token, and token type.

    Raises:
        InvalidCredentialsError: If email or password is incorrect.
        UnauthorizedAccessError: If the email is not verified.
    """

    user = await get_user_by_email(db, user_credentials.email)

    if not user:
        raise InvalidCredentialsError()

    if not await verify_password(user_credentials.password, user.password):
        raise InvalidCredentialsError()
    
    if not user.is_verified:
        raise UnauthorizedAccessError("Email not verified. Please verify your email before logging in.")

    access_token = security.create_access_token(data={"user_id": user.id})
    refresh_token = security.create_refresh_token(data={"user_id": user.id})

    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_pg_db)):
    """
    Verify a user's email using a verification token.

    Validates the token, activates the user's account, and removes
    the verification token from the database.

    Args:
        token: Email verification token.
        db: The asynchronous database session.

    Returns:
        VerifyEmailResponse indicating successful verification.

    Raises:
        VerificationTokenNotFoundError: If token is invalid or expired.
    """
    result = await db.execute(select(User).where(User.verification_token == token))
    user = result.scalar_one_or_none()

    if not user:
        raise VerificationTokenNotFoundError("Invalid or expired verification token")

    user.is_verified = True
    user.verification_token = None

    await db.commit()

    return VerifyEmailResponse(message="Email verified successfully")

@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(payload: RefreshTokenRequest):
    """
    Generate a new access token using a valid refresh token.

    Decodes and validates the refresh token, extracts the user ID,
    and issues a new access token.

    Args:
        payload: Request body containing the refresh token.

    Returns:
        AccessTokenResponse containing a new access token and token type.

    Raises:
        UnauthorizedAccessError: If the refresh token is invalid or expired.
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