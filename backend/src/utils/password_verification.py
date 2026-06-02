# import hashlib
# import bcrypt


# def hash(password: str) -> str:
#     sha256_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
#     salt = bcrypt.gensalt()
#     return bcrypt.hashpw(sha256_hash.encode("utf-8"), salt).decode("utf-8")


# def verify(plain_password: str, hashed_password: str) -> bool:
#     sha256_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
#     return bcrypt.checkpw(sha256_hash.encode("utf-8"), hashed_password.encode("utf-8"))

import asyncio
from passlib.context import CryptContext


pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=False,
)


async def hash_password(password: str) -> str:
    """
    Hash password using Argon2.

    New passwords will use Argon2 automatically.
    """
    return await asyncio.to_thread(
        pwd_context.hash,
        password,
    )


async def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify password against stored hash.

    Supports both:
    - old bcrypt hashes
    - new Argon2 hashes
    """

    return await asyncio.to_thread(
        pwd_context.verify,
        plain_password,
        hashed_password,
    )


def needs_rehash(hashed_password: str) -> bool:
    """
    Check whether stored hash should be upgraded.

    Old bcrypt hashes will return True.
    """
    return pwd_context.needs_update(hashed_password)