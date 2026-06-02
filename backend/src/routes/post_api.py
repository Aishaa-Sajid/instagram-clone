import asyncio
from typing_extensions import Annotated
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.constants import MAX_IMAGES
from src.schemas.post_image import PostImageCreate
from src.dependencies.database import get_pg_db
from src.repositories import post_repo
from src.dependencies.auth import get_current_user
from src.schemas.post import PostResponse, PostCreate
from src.database.models import User
from src.services.cloudinary_service import upload_image
from fastapi import UploadFile, File, Form
from src.utils.file_validators import validate_files
from src.core.exceptions import ValidationError, PostNotFoundError, PermissionDeniedError, TooManyImagesError

router = APIRouter(tags=["Posts"])


@router.get("/", response_model=list[PostResponse])
async def get_posts(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_pg_db),
    limit: int = 10,
    skip: int = 0,
    search: str | None = Query(default=None),
    user_id: int | None = None,
):
    """
    Retrieve posts with pagination and optional filtering.

    Returns posts visible to the authenticated user, supporting:
        - Pagination (limit, skip)
        - Optional caption search
        - Optional filtering by user

    Args:
        current_user: Authenticated user.
        db: Database session dependency.
        limit: Maximum number of posts to return.
        skip: Number of posts to skip for pagination.
        search: Optional search keyword for captions.
        user_id: Optional filter for posts by a specific user.

    Returns:
        List of PostResponse objects.
    """
    return await post_repo.get_posts(
        db=db,
        limit=limit,
        skip=skip,
        search=search,
        viewer_id=current_user.id,
        target_user_id=user_id,
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PostResponse)
async def create_post(
    files: Annotated[list[UploadFile], File(..., description="Upload up to 10 images")],
    caption: Annotated[str, Form(...)],
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new post with images.

    Uploads images to Cloudinary, validates them, and creates a new post
    associated with the authenticated user.

    Args:
        caption: Post caption.
        files: List of image files (max validation handled internally).
        db: Database session dependency.
        current_user: Authenticated user.

    Returns:
        The created PostResponse object.

    Raises:
        ValidationError: If no images are provided or validation fails.
    """
  
    if not files:
        raise ValidationError("At least one image is required")

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


@router.get("/{id}", response_model=PostResponse)
async def get_post(
    id: int,
    db: AsyncSession = Depends(get_pg_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve a single post by ID.

    Fetches a post if it is accessible to the authenticated user.

    Args:
        id: Post ID.
        db: Database session dependency.
        current_user: Authenticated user.

    Returns:
        PostResponse object.

    Raises:
        PostNotFoundError: If post does not exist or is inaccessible.
    """

    return await post_repo.get_post(
        db=db, post_id=id, current_user_id=current_user.id
    )


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
    Update a post's caption and images.

    Supports:
        - Updating caption
        - Deleting existing images
        - Adding new images

    Validates:
        - Post ownership
        - Maximum image limit
        - File validity

    Args:
        id: Post ID.
        caption: Optional updated caption.
        images_to_delete: List of image IDs to remove.
        new_images: New image files to upload.
        db: Database session dependency.
        current_user: Authenticated user.

    Returns:
        Updated PostResponse.

    Raises:
        PostNotFoundError: If post does not exist.
        PermissionDeniedError: If user is not the owner.
        TooManyImagesError: If image limit exceeds allowed maximum.
    """

    post = await post_repo.get_post_by_id(db, id)
    if not post:
        raise PostNotFoundError()

    if post.user_id != current_user.id:
        raise PermissionDeniedError("You are not allowed to update this post")

    remaining_images = [
        img for img in post.images if img.id not in images_to_delete
    ]

    if len(remaining_images) + len(new_images) > MAX_IMAGES:
        raise TooManyImagesError(f"Cannot have more than {MAX_IMAGES} images in a post")

    uploaded_urls = []
    if new_images:
        await validate_files(new_images)
        uploaded_images = await asyncio.gather(
            *[upload_image(file, folder="updated_posts") for file in new_images]
        )
        uploaded_urls = [
            PostImageCreate(image_url=img.url, public_id=img.public_id)
            for img in uploaded_images
        ]
    return await post_repo.update_post_repo(
        db=db,
        post=post,
        caption=caption,
        new_images=uploaded_urls,
        images_to_delete=images_to_delete or [],
    )


@router.delete("/{id}", status_code=204)
async def delete_post(
    id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_pg_db),
):
    """
    Delete a post by ID.

    Only the post owner is allowed to delete the post.

    Args:
        id: Post ID.
        current_user: Authenticated user.
        db: Database session dependency.

    Returns:
        None

    Raises:
        PostNotFoundError: If post does not exist.
        PermissionDeniedError: If user is not the owner.
    """
    post = await post_repo.get_post_by_id(db, id)

    if not post:
        raise PostNotFoundError("Post not found")

    if post.user_id != current_user.id:
        raise PermissionDeniedError("You are not allowed to delete this post")

    await post_repo.delete_post(db, post)

    return
