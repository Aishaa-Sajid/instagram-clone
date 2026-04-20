from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(password: str):
    return pwd_context.hash(password[:72])


def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

#  print("abc") 