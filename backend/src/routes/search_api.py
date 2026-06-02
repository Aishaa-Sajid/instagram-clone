from fastapi import APIRouter, Depends, Query
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

    Performs a fuzzy search using PostgreSQL trigram similarity and
    prefix matching to return ranked user results.

    Args:
        q: Search query string (minimum 1 character).
        limit: Maximum number of results to return (1–50).
        offset: Pagination offset.
        db: Database session dependency.

    Returns:
        List of UserOut objects matching the search criteria.

    Raises:
        UserNotFoundError: If no matching users are found.
    """
  
    users = await user_repo.search_users(db, q, limit, offset)
    return users

