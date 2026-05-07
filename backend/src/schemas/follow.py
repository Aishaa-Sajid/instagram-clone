from pydantic import BaseModel
from src.utils.enum import FollowStatus


class FollowOut(BaseModel):
    id: int
    follower_id: int
    following_id: int
    status: FollowStatus

    model_config = {"from_attributes": True}