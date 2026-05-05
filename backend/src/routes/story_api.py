import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated

from src.dependencies.database import get_pg_db
from src.dependencies.auth import get_current_user
from src.database.models import User
from src.schemas.story import StoryResponse
from src.repositories import story_repo
from src.services.cloudinary.cloudinary_service import upload_image
from src.utils.file_validators import validate_files

router = APIRouter(tags=["Stories"])


@router.post("/", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def create_story(
    file: Annotated[UploadFile, File(...)],
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new story by uploading an image file.

    This endpoint accepts a single image file, validates it, uploads it
    to storage, and creates a story record associated with the current user.

    Args:
        file (UploadFile): Image file to be uploaded as a story.
        db (AsyncSession): Database session dependency.
        current_user (User): Authenticated user creating the story.

    Returns:
        StoryResponse: Created story object containing metadata and media URL.

    """
    try:
        await validate_files([file])

        uploaded = await upload_image(file, folder="stories")

        return await story_repo.create_story(
            db=db,
            user_id=current_user.id,
            media_url=uploaded.url,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create story: {str(e)}")


@router.get("/", response_model=list[StoryResponse])
async def get_stories(
    db: AsyncSession = Depends(get_pg_db),
    _: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
):
    """
    Retrieve active (non-expired) stories.

    This endpoint returns a paginated list of all active stories that have
    not yet expired.

    Args:
        db (AsyncSession): Database session dependency.
        current_user (User): Authenticated user requesting stories.
        skip (int): Number of records to skip for pagination.
        limit (int): Maximum number of stories to return.

    Returns:
        list[StoryResponse]: List of active story objects.

    """
    return await story_repo.get_active_stories(
        db=db,
        skip=skip,
        limit=limit,
    )
