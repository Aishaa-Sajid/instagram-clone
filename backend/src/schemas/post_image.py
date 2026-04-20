from pydantic import BaseModel
from datetime import datetime

class PostImageBase(BaseModel):
    image_url: str


class PostImageCreate(PostImageBase):
    post_id: int


class PostImageResponse(PostImageBase):
    image_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

