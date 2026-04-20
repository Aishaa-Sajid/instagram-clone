from pydantic import BaseModel
from datetime import datetime
from typing import Optional,List
from .user import UserOut
from .post_image import PostImageResponse

class PostBase(BaseModel):
    title: str
    caption: str

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    caption: Optional[str] = None

class PostResponse(PostBase):
    id: int
    created_at: datetime
    owner_id: int
    owner: UserOut
    images: List[PostImageResponse] = []

    model_config = {"from_attributes": True}


class PostOut(BaseModel):
    post: PostResponse
    # likes: int

    model_config = {"from_attributes": True}


#  print("abc")   