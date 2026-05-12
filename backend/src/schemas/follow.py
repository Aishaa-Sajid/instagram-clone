from pydantic import BaseModel
from src.utils.enum import FollowStatus
from src.schemas.user import UserOut


class FollowStatusUpdate(BaseModel):
    status: FollowStatus


class FollowOut(BaseModel):
    id: int
    follower_id: int
    following_id: int
    status: FollowStatus

    model_config = {"from_attributes": True}


class FollowResponse(BaseModel):
    id: int
    follower: UserOut
    following_id: int
    status: FollowStatus

    model_config = {"from_attributes": True}
