from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi.security import HTTPBearer
from src.database.config import settings
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

bearer_scheme = HTTPBearer()

SECRET_KEY: str = settings.SECRET_KEY
REFRESH_SECRET_KEY: str = settings.REFRESH_SECRET_KEY
ALGORITHM: str = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS: int = settings.REFRESH_TOKEN_EXPIRE_DAYS


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def create_access_token(data: dict) -> str:
    """
    Create JWT access token.

    Args:
        data (dict): payload (e.g. {"user_id": 1})

    Returns:
        str: encoded JWT token
    """
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})

    token: str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


def create_refresh_token(data: dict) -> str:

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})

    token = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

    return token


def verify_access_token(token: str) -> dict:
    """
    Decode and validate JWT token.

    Args:
        token (str): JWT token
        credentials_exception: FastAPI HTTPException

    Returns:
        dict: token payload (contains user_id)
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id = payload.get("user_id")
        token_type = payload.get("type")

        if user_id is None:
            raise credentials_exception

        if token_type != "access":
            raise credentials_exception

        return {"user_id": user_id}

    except JWTError:
        raise credentials_exception


def verify_refresh_token(token: str) -> dict:

    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

        user_id = payload.get("user_id")
        token_type = payload.get("type")

        if user_id is None:
            raise credentials_exception

        if token_type != "refresh":
            raise credentials_exception

        return {"user_id": user_id}

    except JWTError:
        raise credentials_exception
