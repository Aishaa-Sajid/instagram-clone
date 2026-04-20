from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_pg_db
from src.repositories import user_repo
from src.schemas.user import UserCreate, UserOut, UserResponse, UserUpdate

router = APIRouter(tags=["Users"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_pg_db)):
    """
    API endpoint to create a new user.
    """

    return await user_repo.create_user(db, user)

  print("abc") #  print("abc")
@router.get("/{id}", response_model=UserOut)
async def get_user(id: int, db: AsyncSession = Depends(get_pg_db)):
    """
    API endpoint to get a user by ID.
    """
    user = await user_repo.get_user_by_id(db, id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} does not exist",
        )

    return user

@router.put("/{id}", response_model=UserOut)
async def update_user(id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_pg_db)):
    """
    API endpoint to update user details.
    """
    user = await user_repo.get_user_by_id(db, id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} does not exist",
        )

    updated_user = await user_repo.update_user(db, id, user_update)

    return updated_user 


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_pg_db)
):
    deleted = await user_repo.delete_user_by_id(db, user_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {"message": f"User {user_id} deleted successfully"}