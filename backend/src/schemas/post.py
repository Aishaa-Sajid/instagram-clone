from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from src.schemas.user import UserOut
from src.schemas.post_image import PostImageCreate, PostImageResponse, PostImageUpdate


class PostBase(BaseModel):
    caption: str | None = None


class PostCreate(PostBase):
    images: List[PostImageCreate] = Field(default_factory=list)


class PostUpdate(BaseModel):
    caption: str | None = None
    images : List[PostImageUpdate] = Field(default_factory=list)    


class PostResponse(PostBase):
    id: int
    created_at: datetime
    updated_at: datetime
    user_id: int
    owner: UserOut
    images: List[PostImageResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class PostOut(BaseModel):
    post: PostResponse
    # likes: int

    model_config = {"from_attributes": True}
