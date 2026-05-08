from pydantic import BaseModel
from datetime import datetime
from src.schemas.user import UserOut


class StoryCreate(BaseModel):
    media_url: str


class StoryResponse(BaseModel):
    id: int
    media_url: str
    created_at: datetime
    user_id: int
    story_owner: UserOut

    model_config = {"from_attributes": True}