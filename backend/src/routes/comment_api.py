from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated

from src.dependencies.database import get_pg_db
from src.dependencies.auth import get_current_user
from src.database.models.user import User

from src.schemas.comment import CommentCreate, CommentUpdate, CommentResponse
from src.repositories import comment_repo
from src.repositories.post_repo import get_post_by_id

router = APIRouter(tags=["Comments"])

@router.post("/post/{post_id}", response_model=CommentResponse, status_code=201)
async def create_comment(
    post_id: int,
    data: CommentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_pg_db),
):
    post = await get_post_by_id(db, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return await comment_repo.create_comment(
        db,
        user_id=current_user.id,
        post_id=post_id,
        data=data,
    )

@router.get("/post/{post_id}", response_model=list[CommentResponse])
async def get_comments_for_post(
    post_id: int,
    db: AsyncSession = Depends(get_pg_db),
    limit: int = 10,
    skip: int = 0,
):
    return await comment_repo.get_comments_by_post(
        db,
        post_id=post_id,
        limit=limit,
        skip=skip,
    )


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_pg_db),
):
    comment = await comment_repo.get_comment_by_id(db, comment_id)

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    return comment

@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    data: CommentUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_pg_db),
):
    comment = await comment_repo.get_comment_by_id(db, comment_id)

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    return await comment_repo.update_comment(
        db,
        comment=comment,
        data=data,
    )

@router.delete("/{comment_id}", status_code=200)
async def delete_comment(
    comment_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_pg_db),
):
    comment = await comment_repo.get_comment_by_id(db, comment_id)

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # comment owner OR post owner
    if not (
        comment.user_id == current_user.id
        or comment.post.user_id == current_user.id
    ):
        raise HTTPException(status_code=403, detail="Not allowed")

    await comment_repo.delete_comment(db, comment=comment)

    return {"message": "Comment deleted successfully"}

@router.get("/user/{user_id}", response_model=list[CommentResponse])
async def get_comments_by_user(
    user_id: int,
    db: AsyncSession = Depends(get_pg_db),
    limit: int = 10,
    skip: int = 0,
):
    return await comment_repo.get_comments_by_user(
        db,
        user_id=user_id,
        limit=limit,
        skip=skip,
    )