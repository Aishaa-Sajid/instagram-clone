from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from src.dependencies.database import get_pg_db
from src.repositories import user_repo
from src.schemas.user import UserCreate, UserOut
from src.services.cloudinary.cloudinary_service import upload_image
from src.dependencies.auth import get_current_user
from typing_extensions import Annotated
from src.database.models import User

router = APIRouter(tags=["Users"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_pg_db)):
    """
    Create a new user in the system.

    This endpoint registers a new user by storing their details in the database.
    The input data is validated before creation.

    Args:
        user (UserCreate): The request body containing user registration details.
        db (AsyncSession): The asynchronous database session.

    Returns:
        UserOut: The created user data.
    """
    try:
        return await user_repo.create_user(db, user)
    except Exception as e:
        return HTTPException(status_code=400, detail=str(e))


@router.get("/{id}", response_model=UserOut)
async def get_user(id: int, db: AsyncSession = Depends(get_pg_db)):
    """
    Retrieve a user by their unique ID.

    This endpoint fetches a user from the database using the provided user ID.
    If the user does not exist, it returns a 404 error.

    Args:
        id (int): The unique identifier of the user to retrieve.
        db (AsyncSession): Database session dependency for async operations.

    Returns:
        UserOut: The user data matching the provided ID.

    Raises:
        HTTPException: 404 error if the user is not found.
    """
    user = await user_repo.get_user_by_id(db, id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} does not exist",
        )

    return user

@router.put("/update-profile", response_model=UserOut)
async def update_user(
    bio: str | None = None,
    is_private: bool | None = None,
    file: UploadFile | None = File(default=None),
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    """
     Update user profile details (authenticated user).

    This endpoint allows an authenticated user to update their profile
    information, including bio, privacy setting, and profile picture.

    If an image file is provided, it is uploaded and the URL is stored
    in the user's profile.

    Args:
        bio (str | None, optional): Updated biography text for the user.
        is_private (bool | None, optional): Privacy setting for the user account.
        file (UploadFile | None, optional): Profile image file to upload.
        db (AsyncSession): The asynchronous database session.
        current_user (User): The currently authenticated user (injected via dependency).

    Returns:
        User: The updated user object.
    """
    user = await user_repo.get_user_by_id(db, current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {current_user.id} does not exist",
        )

    image_url = await upload_image(file, folder="profile_pics") if file else None

    updated_user = await user_repo.update_user(
        db=db,
        user_id=current_user.id,
        bio=bio,
        is_private=is_private,
        image_url=image_url,
    )

    return updated_user


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_pg_db)):
    """
    Delete a user by their ID.

    This endpoint removes a user from the database using their unique ID.
    If no user is found, a 404 error is returned.

    Args:
        user_id (int): The unique identifier of the user to delete.
        db (AsyncSession): The asynchronous database session.

    Returns:
        dict: A confirmation message indicating successful deletion.
    """
    deleted = await user_repo.delete_user_by_id(db, user_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": f"User {user_id} deleted successfully"}
