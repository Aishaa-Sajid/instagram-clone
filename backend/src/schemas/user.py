from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    is_private: Optional[bool] = False
   
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
    is_private: Optional[bool] = False
    created_at: datetime

    model_config = {"from_attributes": True}
    
class UserUpdate(BaseModel):
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
    is_private: Optional[bool] = None


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

