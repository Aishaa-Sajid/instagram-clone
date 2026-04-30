from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from src.schemas.user import UserOut, UserResponse
from src.schemas.post_image import PostImageCreate, PostImageResponse, PostImageUpdate
from src.schemas.like import LikeResponse


class PostBase(BaseModel):
    caption: str | None = None


class PostCreate(PostBase):
    images: List[PostImageCreate] = Field(default_factory=list)


class PostUpdate(BaseModel):
    caption: str | None = None
    new_images: List[PostImageCreate] = Field(default_factory=list)
    images_to_delete: list[int] | None = None


class PostResponse(PostBase):
    id: int
    created_at: datetime
    updated_at: datetime
    user_id: int
    owner: UserOut
    images: List[PostImageResponse] = Field(default_factory=list)
    likes_count: int = 0
    is_liked: bool = False
    model_config = {"from_attributes": True}


# class PostOut(BaseModel):
#     post: PostResponse
#     likes: LikeResponse

#     model_config = {"from_attributes": True}
