from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_pg_db
from src.repositories import user_repo
from src.schemas.user import UserCreate, UserOut, UserUpdate
from src.services.Cloudinary.cloudinary_service import upload_image
from src.core.security import get_current_user
import json

router = APIRouter(tags=["Users"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_pg_db)):
    """
    API endpoint to create a new user.
    """

    return await user_repo.create_user(db, user)



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


# @router.put("/upload-profile-picture")
# async def upload_profile_picture(
#     file: UploadFile,
#     db: AsyncSession = Depends(get_pg_db),
#     current_user=Depends(get_current_user),
# ):

#     # image_bytes = await file
#     image_url = await upload_image(file)

#     user = await user_repo.update_profile_picture(db, current_user.id, image_url)

#     return {"message": "Profile picture updated", "url": image_url}


# @router.put("/{id}", response_model=UserOut)
# async def update_user(
#     id: int,
#     file: UploadFile | None = File(default=None),
#     user_update: UserUpdate | None = None,
#     db: AsyncSession = Depends(get_pg_db),
#     current_user=Depends(get_current_user),
# ):
    
#     if current_user.id != id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not authorized"
#         )
#     """
#     API endpoint to update user details.
#     """
#     user = await user_repo.get_user_by_id(db, id)

#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"User with id {id} does not exist",
#         )

#     update_data = None
#     if user_update:
#         try:
#             update_data = UserUpdate(**json.loads(user_update))
#         except Exception:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid user_update JSON"
#             )

#     # image_bytes = await file
#     if file: 
#         image_url = await upload_image(file)
#     else:
#         image_url = None

#     updated_user = await user_repo.update_user(db, id, user_update, image_url)

#     return updated_user


@router.put("/{id}", response_model=UserOut)
async def update_user(
    id: int,
    file: UploadFile | None = File(default=None),
    user_update: str | None = Form(default=None),
    db: AsyncSession = Depends(get_pg_db),
    current_user=Depends(get_current_user),
):
    # 🔐 authorization
    if current_user.id != id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    user = await user_repo.get_user_by_id(db, id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} does not exist",
        )

    # 🧠 clean + protected
    update_data = None
    if user_update:
        try:
            update_data = UserUpdate(**json.loads(user_update))
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid user_update JSON"
            )

    # 🖼️ upload image if present
    image_url = await upload_image(file) if file else None

    # 🚀 update user
    updated_user = await user_repo.update_user(
        db,
        id,
        update_data,
        image_url
    )

    return updated_user


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_pg_db)):
    deleted = await user_repo.delete_user_by_id(db, user_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": f"User {user_id} deleted successfully"}
