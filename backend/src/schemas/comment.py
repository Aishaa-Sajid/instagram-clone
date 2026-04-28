from pydantic import BaseModel, Field
from datetime import datetime
# from src.schemas.user import UserOut

class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class CommentResponse(BaseModel):
    id: int
    content: str
    user_id: int
    post_id: int
    created_at: datetime
    updated_at: datetime
    # user:UserOut

    model_config = {"from_attributes": True}