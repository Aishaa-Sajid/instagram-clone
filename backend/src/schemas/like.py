from pydantic import BaseModel


class LikeResponse(BaseModel):
    liked: bool
    likes_count: int
