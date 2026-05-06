from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.dependencies.database import get_pg_db
from src.repositories import user_repo
from src.schemas.user import UserOut

router = APIRouter(tags=["Search"])


@router.get("/users", response_model=List[UserOut])
async def search_users(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_pg_db),
):
    """
    Search users by username.

    This endpoint allows users to search for other users using a query string.
    It performs a fuzzy search using PostgreSQL trigram similarity and returns
    ranked results.

    Args:
        q (str): Search query string.
        limit (int, optional): Maximum number of results to return.
        offset (int, optional): Pagination offset.
        db (AsyncSession): Database session dependency.

    Returns:
        List[UserOut]: List of matching users.

    Raises:
        HTTPException: If search operation fails.
    """
    try:
        users = await user_repo.search_users(db, q, limit, offset)
        return users

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed",
        )