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
    Upload a new story.

    Accepts a single image file and stores it as a story.
    """
    try:
        # await validate_files([file])

        uploaded = await upload_image(file, folder="stories")

        return await story_repo.create_story(
            db=db,
            user_id=current_user.id,
            media_url=uploaded.url,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create story: {str(e)}"
        )


@router.get("/", response_model=list[StoryResponse])
async def get_stories(
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
):
    """
    Get all active stories (not expired).
    """
    return await story_repo.get_active_stories(
        db=db,
        skip=skip,
        limit=limit,
    )