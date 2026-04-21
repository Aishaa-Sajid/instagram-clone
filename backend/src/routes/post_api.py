from typing_extensions import Annotated

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.database.dependency import get_pg_db
from src.repositories import post_repo
from sqlalchemy import select
from src.core.security import get_current_user
from src.schemas.post import PostResponse, PostCreate, PostOut
from src.database.models import Post, User

router = APIRouter(tags=["Posts"])


@router.get("/", response_model=list[PostOut])
async def get_posts(
    _: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_pg_db),
    limit: int = 10,
    skip: int = 0,
    search: str | None = Query(default=None),
):
    """
    Retrieve a list of posts with pagination and optional search filtering.

    This endpoint returns posts for an authenticated user. Results can be
    paginated using `limit` and `skip`, and optionally filtered using a
    search query.

    Args:
        _ (User): The currently authenticated user (injected via dependency).
        db (AsyncSession): The asynchronous database session.
        limit (int, optional): Maximum number of posts to return. Defaults to 10.
        skip (int, optional): Number of posts to skip for pagination. Defaults to 0.
        search (str | None, optional): Optional search keyword to filter posts.
            Defaults to None.

    Returns:
        list[PostOut]: A list of posts matching the given criteria.

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
    Retrieve a list of posts without authentication.

    This endpoint returns posts in a paginated format and allows optional
    filtering using a search query. It is publicly accessible and does not
    require user authentication.

    Args:
        db (AsyncSession): The asynchronous database session.
        limit (int, optional): Maximum number of posts to return. Defaults to 10.
        skip (int, optional): Number of posts to skip for pagination. Defaults to 0.
        search (str | None, optional): Optional search keyword to filter posts.
            Defaults to None.

    Returns:
        list[PostOut]: A list of posts matching the given criteria.
    """
    return await post_repo.get_posts(db, limit, skip, search)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PostResponse)
async def create_post(
    post: PostCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_pg_db),
):
    """
    Create a new post for the authenticated user.

    This endpoint allows an authenticated user to create a new post.
    The provided post data is validated and stored in the database.

    Args:
        post (PostCreate): The request body containing post details.
        current_user (User): The currently authenticated user (injected via dependency).
        db (AsyncSession): The asynchronous database session.

    Returns:
        PostResponse: The created post with full details.
    """
    return await post_repo.create_post(db, post, current_user.id)


@router.get("/{id}", response_model=PostOut)
async def get_post(
    id: int,
    db: AsyncSession = Depends(get_pg_db),
    _=Depends(get_current_user),
):
    """
    Retrieve a single post by its ID.

    This endpoint fetches a specific post using its unique identifier.
    Authentication is required to access this route. If the post does not
    exist, a 404 error is returned.

    Args:
        id (int): The unique identifier of the post.
        db (AsyncSession): The asynchronous database session.
        _ (User): The currently authenticated user (injected via dependency).

    Returns:
        PostOut: The requested post data.
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
    Delete a post by its ID (owner only).

    This endpoint allows an authenticated user to delete a post they own.
    It first verifies that the post exists and then checks whether the
    requesting user is the owner before performing the deletion.

    Args:
        id (int): The unique identifier of the post to delete.
        current_user (User): The currently authenticated user (injected via dependency).
        db (AsyncSession): The asynchronous database session.

    Returns:
        bool: True if the post was successfully deleted.
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
    db: AsyncSession = Depends(get_pg_db),
):
    """
    Update an existing post by its ID (owner only).

    This endpoint allows an authenticated user to update a post they own.
    It verifies that the post exists and checks ownership before applying
    the updates.

    Args:
        id (int): The unique identifier of the post to update.
        updated_post (PostCreate): The request body containing updated post data.
        current_user (User): The currently authenticated user (injected via dependency).
        db (AsyncSession): The asynchronous database session.

    Returns:
        PostResponse: The updated post with full details.
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
