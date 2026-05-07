from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.dependencies.database import get_pg_db
from src.dependencies.auth import get_current_user
from src.database.models.user import User
from src.repositories import follow_repo
from src.schemas.follow import FollowOut

router = APIRouter(tags=["Follow"])


@router.post("/{user_id}", response_model=FollowOut)
async def follow_user(
    user_id: int,
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    return await follow_repo.follow_user(db, current_user, user_id)


@router.delete("/{user_id}", status_code=204)
async def unfollow_user(
    user_id: int,
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    return await follow_repo.unfollow_user(db, current_user, user_id)


@router.get("/requests", response_model=list[FollowOut])
async def get_follow_requests(
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    return await follow_repo.get_follow_requests(db, current_user)


@router.post("/requests/{follower_id}/accept", response_model=FollowOut)
async def accept_follow_request(
    follower_id: int,
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    return await follow_repo.accept_follow_request(db, current_user, follower_id)


@router.post("/requests/{follower_id}/reject", response_model=FollowOut)
async def reject_follow_request(
    follower_id: int,
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    return await follow_repo.reject_follow_request(db, current_user, follower_id)
