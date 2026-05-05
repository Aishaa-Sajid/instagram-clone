import asyncio
from typing_extensions import Annotated
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.constants import MAX_IMAGES
from src.schemas.post_image import PostImageCreate
from src.dependencies.database import get_pg_db
from src.repositories import post_repo
from src.dependencies.auth import get_current_user
from src.schemas.post import PostResponse, PostCreate
from src.database.models import User
from src.services.cloudinary.cloudinary_service import upload_image
from fastapi import UploadFile, File, Form
from src.utils.file_validators import validate_files

router = APIRouter(tags=["Posts"])


@router.get("/", response_model=list[PostResponse])
async def get_posts(
    current_user: Annotated[User, Depends(get_current_user)],
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
        list[PostResponse]: A list of posts matching the given criteria.

    """
    return await post_repo.get_posts(
        db=db, limit=limit, skip=skip, search=search, user_id=current_user.id
    )


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
    try:
        if not files:
            raise HTTPException(
                status_code=400, detail="At least one image is required"
            )

        await validate_files(files)

        upload_tasks = [upload_image(file, folder="post_images") for file in files]
        image_urls = await asyncio.gather(*upload_tasks)

        post_data = PostCreate(
            caption=caption,
            images=[
                PostImageCreate(image_url=img.url, public_id=img.public_id)
                for img in image_urls
            ],
        )

        return await post_repo.create_post(
            db=db, post=post_data, user_id=current_user.id
        )

    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error occurred")


@router.get("/{id}", response_model=PostResponse)
async def get_post(
    id: int,
    db: AsyncSession = Depends(get_pg_db),
    current_user=Depends(get_current_user),
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
        PostResponse: The requested post data.
    """

    post = await post_repo.get_post(db=db, post_id=id, user_id=current_user.id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id {id} not found"
        )

    return post


@router.put("/{id}", response_model=PostResponse)
async def update_post(
    id: int,
    caption: str | None = Form(None),
    images_to_delete: list[int] = Form(default=[]),
    new_images: list[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
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
    post = await post_repo.get_post_by_id(db, id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    remaining_images = [img for img in post.images if img.id not in images_to_delete]

    if len(remaining_images) + len(new_images) > MAX_IMAGES:
        raise HTTPException(status_code=400, detail="Max 10 images allowed")

    try:
        uploaded_urls = []
        if new_images:
            await validate_files(new_images)
            uploaded_urls = await asyncio.gather(
                *[upload_image(file, folder="updated_posts") for file in new_images]
            )

        updated_post = await post_repo.update_post_repo(
            db=db,
            post=post,
            caption=caption,
            new_images=uploaded_urls,
            images_to_delete=images_to_delete or [],
        )

        if not updated_post:
            raise HTTPException(status_code=404, detail="Post not found")

        return updated_post

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected error occurred: {str(e)}"
        )


@router.delete("/{id}", status_code=204)
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
    try:
        post = await post_repo.get_post_by_id(db, id)

        if not post:
            raise HTTPException(status_code=404, detail="post not found")

        if post.user_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="You are not allowed to delete this post"
            )

        await post_repo.delete_post(db, post)

        return

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected error occurred: {str(e)}"
        )
