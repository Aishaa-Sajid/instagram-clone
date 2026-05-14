from pydantic import BaseModel, Field
from datetime import datetime
from src.schemas.user import UserPreview

class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class CommentResponse(BaseModel):
    id: int
    content: str
    user_id: int
    post_id: int
    user: UserPreview
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}