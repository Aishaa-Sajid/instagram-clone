from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from src.utils.enum import FollowStatus


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=5, max_length=40)
    password: str = Field(..., min_length=8, max_length=32)
    is_private: bool = False


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UpdatePasswordSchema(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=32)
    confirm_password: str = Field(min_length=8, max_length=32)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str
    bio: str | None
    profile_picture: str | None
    is_private: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileOut(BaseModel):
    user: UserOut
    followers_count: int = 0
    following_count: int = 0
    follow_status: FollowStatus | None = None

    model_config = {"from_attributes": True}

class UserPreview(BaseModel):
    id: int
    username: str
    profile_picture: str | None

    model_config = {"from_attributes": True}
