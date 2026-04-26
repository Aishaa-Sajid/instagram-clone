from typing import Optional

from pydantic import BaseModel
from datetime import datetime

class PostImageBase(BaseModel):
    image_url: str


class PostImageCreate(PostImageBase):
    public_id: str

class PostImageUpdate(BaseModel):
    id: int| None = None   
    image_url: str             

class PostUploadImage(BaseModel):
    url:str
    public_id:str
    
class PostImageResponse(PostImageBase):
    id: int
    image_url: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

