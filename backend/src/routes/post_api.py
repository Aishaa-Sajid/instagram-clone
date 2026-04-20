from typing_extensions import Annotated

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.database.dependency import get_pg_db
from src.repositories import post_repo
from sqlalchemy import select
from src.core.security import get_current_user
from src.schemas.post import PostResponse, PostCreate, PostOut
from src.database.models import Post,User

router = APIRouter(tags=["Posts"])
#  print("abc") 

@router.get("/", response_model=list[PostOut])
async def get_posts(
    _: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_pg_db),
    limit: int = 10,
    skip: int = 0,
    search: str | None = Query(default=None),
):
    """
    Get all posts with pagination and search.
    """
    return await post_repo.get_posts(db, limit, skip, search)


@router.get("/no_auth", response_model=list[PostOut])
async def get_posts_no_auth(
    db: AsyncSession = Depends(get_pg_db),
    limit: int = 10,
    skip: int = 0,
    search: str | None = Query(default=None),
):
    """
    Get all posts with pagination and search.
    """
    return await post_repo.get_posts(db, limit, skip, search)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PostResponse)
async def create_post(
    post: PostCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_pg_db)
):
    """
    Create a new post.
    """
    return await post_repo.create_post(db, post, current_user.id)


@router.get("/{id}", response_model=PostOut)
async def get_post(
    id: int,
    db: AsyncSession = Depends(get_pg_db),
    _=Depends(get_current_user),
):
    """
    Get single post by ID.
    """
    
    post = await post_repo.get_post(db, id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id {id} not found"
        )

    return post


@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_post(
    id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_pg_db),
):
    
    """
    Delete post (owner only).
    """

    stmt = select(Post).options(selectinload(Post.owner)).where(Post.id == id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="post not found")

    if post.owner_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You are not allowed to delete this post"
        )

    return await post_repo.delete_post(db, post)


@router.put("/{id}", response_model=PostResponse)
async def update_post(
    id: int,
    updated_post: PostCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_pg_db)
    
    
):
    """
    Update post (owner only).
    """
    stmt = select(Post).options(selectinload(Post.owner)).where(Post.id == id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="post not found")

    if post.owner_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You are not allowed to update this post"
        )

    updated = await post_repo.update_post(db, id, updated_post.model_dump())

    return updated
