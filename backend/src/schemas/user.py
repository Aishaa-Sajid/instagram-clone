from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=5, max_length=40)
    password: str = Field(..., min_length=8, max_length=50)
    is_private: bool = False


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str
    bio: str | None
    profile_picture: str | None
    is_private: bool
    created_at: datetime

    model_config = {"from_attributes": True}
