import hashlib
import bcrypt


def hash(password: str) -> str:
    sha256_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(sha256_hash.encode("utf-8"), salt).decode("utf-8")


def verify(plain_password: str, hashed_password: str) -> bool:
    sha256_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return bcrypt.checkpw(sha256_hash.encode("utf-8"), hashed_password.encode("utf-8"))
