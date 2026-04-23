import asyncio
from typing import List
from typing_extensions import Annotated
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.database.models.post_image import PostImage
from src.schemas.post_image import PostImageCreate
from src.dependencies.database import get_pg_db
from src.repositories import post_repo
from sqlalchemy import select
from src.dependencies.auth import get_current_user
from src.schemas.post import PostResponse, PostCreate, PostOut, PostUpdate
from src.database.models import Post, User
from src.services.Cloudinary.cloudinary_service import upload_image
from fastapi import UploadFile, File, Form

router = APIRouter(tags=["Posts"])


@router.get("/", response_model=list[PostResponse])
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


# @router.get("/no_auth", response_model=list[PostResponse])
# async def get_posts_no_auth(
#     db: AsyncSession = Depends(get_pg_db),
#     limit: int = 10,
#     skip: int = 0,
#     search: str | None = Query(default=None),
# ):
#     """
#     Retrieve a list of posts without authentication.

#     This endpoint returns posts in a paginated format and allows optional
#     filtering using a search query. It is publicly accessible and does not
#     require user authentication.

#     Args:
#         db (AsyncSession): The asynchronous database session.
#         limit (int, optional): Maximum number of posts to return. Defaults to 10.
#         skip (int, optional): Number of posts to skip for pagination. Defaults to 0.
#         search (str | None, optional): Optional search keyword to filter posts.
#             Defaults to None.

#     Returns:
#         list[PostOut]: A list of posts matching the given criteria.
#     """
#     return await post_repo.get_posts(db, limit, skip, search)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PostResponse)
async def create_post(
    files: Annotated[list[UploadFile], File(..., description="Upload up to 10 images")],
    caption: Annotated[str, Form(...)],
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new post for the authenticated user.

    This endpoint allows an authenticated user to create a new post.
    The provided post data is validated and stored in the database.

    Args:
        caption (str): The caption for the new post.
        files (list[UploadFile]): The list of image files to upload.
        current_user (User): The currently authenticated user (injected via dependency).
        db (AsyncSession): The asynchronous database session.

    Returns:
        PostResponse: The created post with full details
    """
    if not files:
        raise HTTPException(status_code=400, detail="At least one image is required")

    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 images allowed")

    upload_tasks = [upload_image(file, folder="post_images") for file in files]
    image_urls = await asyncio.gather(*upload_tasks)

    post_data = PostCreate(
        caption=caption,
        images=[PostImageCreate(image_url=url) for url in image_urls],
    )

    return await post_repo.create_post(db=db, post=post_data, user_id=current_user.id)


@router.get("/{id}", response_model=PostResponse)
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


@router.put("/{id}", response_model=PostResponse)
async def update_post(
    id: int,
    caption: str | None = Form(None),
    images_to_delete: list[int] = Form(default_factory=list),
    new_images: list[UploadFile] = File(default_factory=list),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: AsyncSession = Depends(get_pg_db),
):
    """
    Update a post including caption and images.

    This endpoint allows partial updates to a post. It supports updating
    the caption, deleting selected images, and uploading new images. New
    images are uploaded asynchronously before being associated with the
    post.

    The function delegates the core update logic to the repository layer
    after preparing the uploaded image URLs and converting them into
    PostImage objects.

    Args:
        id (int): ID of the post to update.
        caption (str | None): Optional updated caption for the post.
        images_to_delete (list[int]): List of image IDs to remove from
            the post.
        new_images (list[UploadFile]): List of new image files to upload
            and attach to the post.
        current_user (User): Authenticated user performing the request.
        db (AsyncSession): Asynchronous database session dependency.

    Returns:
        PostResponse: The updated post data after successful modification.
    """
    uploaded_urls = []

    if new_images:
        uploaded_urls = await asyncio.gather(
            *[upload_image(file, folder="updated_posts") for file in new_images]
        )

    post_image_objs = [PostImage(image_url=url) for url in uploaded_urls]

    return await post_repo.update_post_repo(
        db=db,
        post_id=id,
        user_id=current_user.id,
        caption=caption,
        new_images=post_image_objs,
        images_to_delete=images_to_delete,
    )


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
    post = await post_repo.get_post_by_id(db, id)

    if not post:
        raise HTTPException(status_code=404, detail="post not found")

    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You are not allowed to delete this post"
        )

    await post_repo.delete_post(db, post)
