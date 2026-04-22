import hashlib

import bcrypt
from passlib.context import CryptContext


def hash(password: str) -> str:
    sha256_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(sha256_hash.encode("utf-8"), salt).decode("utf-8")

def verify(plain_password: str, hashed_password: str) -> bool:
    sha256_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return bcrypt.checkpw(sha256_hash.encode("utf-8"), hashed_password.encode("utf-8"))

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# def hash(password: str):
#     return pwd_context.hash(password[:72])

# def verify(plain_password, hashed_password):
#     return pwd_context.verify(plain_password, hashed_password)

