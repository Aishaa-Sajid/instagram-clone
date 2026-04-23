from typing import Optional

from pydantic import BaseModel
from datetime import datetime

class PostImageBase(BaseModel):
    image_url: str


class PostImageCreate(PostImageBase):
    pass

class PostImageUpdate(BaseModel):
    id: int| None = None   
    image_url: str             

class PostImageResponse(PostImageBase):
    id: int
    image_url: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

