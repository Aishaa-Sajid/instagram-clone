from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated
from src.dependencies.database import get_pg_db
from src.dependencies.auth import get_current_user
from src.database.models import User
from src.schemas.story import StoryResponse
from src.repositories import story_repo
from src.services.cloudinary_service import upload_image
from src.utils.file_validators import validate_files

router = APIRouter(tags=["Stories"])


@router.post("/", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def create_story(
    file: Annotated[UploadFile, File(...)],
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new story by uploading an image.

    Uploads the provided image to storage and creates a story record
    linked to the authenticated user.

    Args:
        file: Image file to be uploaded as a story.
        db: Database session dependency.
        current_user: Authenticated user creating the story.

    Returns:
        StoryResponse containing story metadata and media URL.

    Raises:
        ValidationError: If file validation fails.
    """
    await validate_files([file])

    uploaded = await upload_image(file, folder="stories")

    return await story_repo.create_story(
        db=db,
        user_id=current_user.id,
        media_url=uploaded.url,
        public_id=uploaded.public_id,
    )


@router.get("/", response_model=list[StoryResponse])
async def get_stories(
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
):
    """
    Retrieve active (non-expired) stories.

    Returns a paginated list of stories that are still active (created
    within the last 24 hours) and accessible to the authenticated user.

    Args:
        db: Database session dependency.
        current_user: Authenticated user requesting stories.
        skip: Number of records to skip for pagination.
        limit: Maximum number of stories to return.

    Returns:
        List of StoryResponse objects.

    Notes:
        - Only active (non-expired) stories are included.
        - Visibility depends on follow/privacy rules.
    """

    stories = await story_repo.get_active_stories(
        db=db, skip=skip, limit=limit, viewer_id=current_user.id
    )
    return stories
