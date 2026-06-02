from datetime import datetime
from pydantic import BaseModel
from src.schemas.user import UserPreview

class LikeResponse(BaseModel):
    liked: bool
    likes_count: int

class LikeOut(BaseModel):
    id: int
    user_id: int
    post_id: int
    user: UserPreview
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}