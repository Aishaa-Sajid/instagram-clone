from fastapi import APIRouter, Depends,status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from src.dependencies.database import get_pg_db
from src.repositories import user_repo
from src.schemas.user import UpdatePasswordSchema, UserCreate, UserOut, UserProfileOut
from src.services.cloudinary_service import upload_image
from src.dependencies.auth import get_current_user
from src.database.models import User
from src.core.exceptions import UnauthorizedAccessError

router = APIRouter(tags=["Users"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_pg_db)):
    """
    Create a new user.

    Registers a new user by validating input data and storing it in the database.

    Args:
        user: User registration payload.
        db: Database session dependency.

    Returns:
        UserOut representing the created user.

    Raises:
        ConflictError: If email already exists.
    """

    return await user_repo.create_user(db, user)


@router.get("/me", response_model=UserProfileOut)
async def get_current_user_profile(
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve the profile of the authenticated user.

    Returns user profile data along with follower statistics.

    Args:
        db: Database session dependency.
        current_user: Authenticated user.

    Returns:
        UserProfileOut containing:
            - user data
            - follower count
            - following count
            - follow status
    """
    followers_count,following_count,follow_status = await user_repo.get_follow_stats(db=db, user_id=current_user.id, current_user_id=current_user.id)
    return UserProfileOut(
        user=current_user,
        followers_count=followers_count,
        following_count=following_count,
        follow_status=follow_status
    )


@router.get("/{id}", response_model=UserProfileOut)
async def get_user(
    id: int,
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a user profile by ID.

    Fetches user details along with follow statistics and visibility rules.

    Args:
        id: User ID.
        db: Database session dependency.
        current_user: Authenticated user.

    Returns:
        UserProfileOut object.

    Raises:
        UserNotFoundError: If user does not exist.
    """

    return await user_repo.get_user_profile(
            db=db, user_id=id, current_user_id=current_user.id
        )

@router.put("/update-profile", response_model=UserOut)
async def update_user(
    bio: str | None = None,
    is_private: bool | None = None,
    file: UploadFile | None = File(default=None),
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update authenticated user's profile.

    Allows updating:
        - bio
        - privacy setting
        - profile picture

    Uploads image to cloud storage if provided.

    Args:
        bio: Optional updated biography.
        is_private: Optional privacy setting.
        file: Optional profile image.
        db: Database session dependency.
        current_user: Authenticated user.

    Returns:
        Updated User object.

    Raises:
        ExternalServiceError: If image upload fails.
    """
    result = await upload_image(file, folder="profile_pics") if file else None

    image_url = result.url if result else None
    public_id = result.public_id if result else None

    return await user_repo.update_user(
        db=db,
        user=current_user,
        bio=bio,
        is_private=is_private,
        image_url=image_url,
        public_id=public_id,
    )




@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_pg_db),current_user:User=Depends(get_current_user)):
    """
    Soft delete a user account.

    Deletes a user only if the authenticated user matches the target ID.

    Args:
        user_id: ID of the user to delete.
        db: Database session dependency.
        current_user: Authenticated user.

    Returns:
        Success message.

    Raises:
        UnauthorizedAccessError: If user tries to delete another account.
        UserNotFoundError: If user does not exist.
    """
    if current_user.id != user_id:
        raise UnauthorizedAccessError(
            "You are not allowed to delete this user"
        )
    await user_repo.delete_user_by_id(db, user_id)

    return {"message": f"User {user_id} deleted successfully"}




@router.put("/update-password")
async def update_password(
    payload: UpdatePasswordSchema,
    db: AsyncSession = Depends(get_pg_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update the authenticated user's password.

    Validates current password before updating to a new password.

    Args:
        payload: Current and new password schema.
        db: Database session dependency.
        current_user: Authenticated user.

    Returns:
        Success message.

    Raises:
        ValidationError: If current password is incorrect or invalid.
    """
    return await user_repo.update_password(
        db=db,
        user=current_user,
        payload=payload,
    )

   
