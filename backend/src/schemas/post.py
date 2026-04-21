from pydantic import BaseModel,Field
from datetime import datetime
from typing import Optional,List
from .user import UserOut
from .post_image import PostImageCreate, PostImageResponse

class PostBase(BaseModel):
    caption: str

class PostCreate(PostBase):
    images: List[PostImageCreate] = []

class PostUpdate(BaseModel):
    caption: str | None = None

class PostResponse(PostBase):
    id: int
    created_at: datetime
    user_id: int
    owner: UserOut
    images: List[PostImageResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class PostOut(BaseModel):
    post: PostResponse
    # likes: int

    model_config = {"from_attributes": True}


