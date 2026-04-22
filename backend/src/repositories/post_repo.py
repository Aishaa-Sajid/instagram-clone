from fastapi import HTTPException, Response,status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.database.models.post_image import PostImage
from src.schemas.post import PostCreate

# from src.database.models.vote import Vote
from src.database.models.post import Post

async def get_post_by_id(db: AsyncSession, post_id: int):
    stmt = (
        select(Post)
        .options(
            selectinload(Post.owner),
            selectinload(Post.images)
        )
        .where(Post.id == post_id)
    )

    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_posts(db: AsyncSession, limit: int, skip: int, search: str | None = None):
    
    """
        Retrieve a paginated list of posts with optional search filtering.

    This function queries the database for posts using SQLAlchemy 2.0 async
    style. It supports pagination and optional filtering by post caption.
    Related entities such as the post owner and images are eagerly loaded
    using `selectinload` to avoid N+1 query issues.

    Args:
        db (AsyncSession): The asynchronous database session used for querying.
        limit (int): Maximum number of posts to return.
        skip (int): Number of posts to skip (used for pagination).
        search (str | None, optional): Optional search string to filter posts
            by caption (case-insensitive partial match). Defaults to None.

    Returns:
        list[dict]: A list of dictionaries, each containing a post object
        under the key "post".
    """
    stmt = (
        select(Post)
        .options(selectinload(Post.owner), selectinload(Post.images))
        .limit(limit)
        .offset(skip)
    )

    if search:
        stmt = stmt.where(Post.caption.ilike(f"%{search}%"))

    result = await db.execute(stmt)

    posts = [{"post": post} for post in result.scalars().all()]

    return posts


async def create_post(db: AsyncSession, post: PostCreate, user_id: int) -> Post:
    """
    Create a new post along with its associated images.

    This function inserts a new post into the database for the given user,
    attaches up to 10 images to the post, and returns the fully populated
    post including its owner and images.

    Args:
        db (AsyncSession): The asynchronous database session.
        post (PostCreate): The post data containing caption and list of images.
        user_id (int): The ID of the user creating the post.

    Returns:
        Post: The newly created post with related images and owner loaded.

    """
    if len(post.images) > 10:
        raise Exception("A post can have maximum 10 images")

    new_post = Post(caption=post.caption, user_id=user_id)

    db.add(new_post)
    await db.flush()

    images = [
        PostImage(post_id=new_post.id, image_url=image.image_url)
        for image in post.images
    ]

    db.add_all(images)
    await db.commit()
    await db.refresh(new_post)

    result = await db.execute(
        select(Post)
        .options(selectinload(Post.images), selectinload(Post.owner))
        .where(Post.id == new_post.id)
    )

    new_post = result.scalar_one()
    return new_post


async def get_post(db: AsyncSession, post_id: int):
    """
    Fetch single post with vote count.
    """
    post = await get_post_by_id(db, post_id)

    if not post:
        return None

    return {"post": post}


async def delete_post(db: AsyncSession, post: Post):
    """
    Delete a post instance.
    """
    # stmt = select(Post).options(selectinload(Post.owner)).where(Post.id == id)
    # result = await db.execute(stmt)
    # post = result.scalar_one_or_none()

    await db.delete(post)
    await db.commit()

    # return {"message": "Post deleted successfully"}
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def update_post(db: AsyncSession, post_id: int, caption: str | None = None):
    """
    Update post using async SQLAlchemy 2.0 style.
    """
  
    post = await get_post_by_id(db, post_id)

    if caption is not None:
        post.caption = caption

    await db.commit()
    await db.refresh(post)

    return post
