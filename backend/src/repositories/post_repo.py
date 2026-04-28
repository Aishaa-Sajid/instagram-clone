from fastapi import HTTPException, Response, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.database.models.post_image import PostImage
from src.schemas.post import PostCreate, PostResponse, PostUpdate
from src.utils.constants import MAX_IMAGES
from src.database.models.post import Post
from src.repositories.post_image_repo import _add_post_images, _delete_post_images


async def get_post_by_id(db: AsyncSession, post_id: int) -> Post | None:
    stmt = (
        select(Post)
        .options(
            selectinload(Post.owner),
            selectinload(Post.images),
            selectinload(Post.likes),
        )
        .where(Post.id == post_id)
    )

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_posts(
    db: AsyncSession,
    *,
    limit: int,
    skip: int,
    user_id: int,
    search: str | None = None,
) -> list[Post]:
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
        list[Post]: A list of post objects.
    """
    stmt = (
        select(Post)
        .options(
            selectinload(Post.owner),
            selectinload(Post.images),
            selectinload(Post.likes),
        )
        .limit(limit)
        .offset(skip)
    )

    if search:
        stmt = stmt.where(Post.caption.ilike(f"%{search}%"))

    result = await db.execute(stmt)
    posts = result.scalars().all()
    response = []

    for post in posts:
        likes_count = len(post.likes)

        is_liked = False
        if user_id:
            is_liked = any(like.user_id == user_id for like in post.likes)

        response.append(
            PostResponse(
                id=post.id,
                caption=post.caption,
                created_at=post.created_at,
                updated_at=post.updated_at,
                user_id=post.user_id,
                owner=post.owner,
                images=post.images,
                likes_count=likes_count,
                is_liked=is_liked,
            )
        )

    return response


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
    if len(post.images) > MAX_IMAGES:
        raise Exception(f"A post can have maximum {MAX_IMAGES} images")

    try:

        new_post = Post(caption=post.caption, user_id=user_id)
        db.add(new_post)
        await db.flush()

        images = [
            PostImage(
                post_id=new_post.id,
                image_url=image.image_url,
                public_id=image.public_id,
            )
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

        return result.scalar_one()

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create post: {str(e)}")


async def get_post(db: AsyncSession, post_id: int, user_id: int) -> PostResponse | None:
    """
    Retrieve a single post by its ID.

    This function fetches a post from the database using the provided
    post ID. If the post does not exist, it returns None.

    Args:
        db (AsyncSession): Asynchronous database session used for the
            query operation.
        post_id (int): ID of the post to retrieve.

    Returns:
        Post | None: The post instance if found, otherwise None.
    """
    post = await get_post_by_id(db, post_id)

    if not post:
        return None

    # return post
    likes_count = len(post.likes)

    is_liked = any(like.user_id == user_id for like in post.likes)

    return PostResponse(
        id=post.id,
        caption=post.caption,
        created_at=post.created_at,
        updated_at=post.updated_at,
        user_id=post.user_id,
        owner=post.owner,
        images=post.images,
        likes_count=likes_count,
        is_liked=is_liked,
    )


async def delete_post(db: AsyncSession, post: Post):
    """
    Delete a post from the database.

    This function removes the given post instance from the database and
    commits the transaction. It returns an empty response with a 204
    status code upon successful deletion.

    Args:
        db (AsyncSession): Asynchronous database session used for the
            delete operation.
        post (Post): The post instance to be deleted.

    Returns:
        Response: An empty HTTP response with status code 204 (No Content).
    """

    await db.delete(post)
    await db.commit()


async def update_post_repo(
    db: AsyncSession,
    post: Post,
    user_id: int,
    caption: str | None,
    new_images: list,
    images_to_delete: list[int],
) -> Post | None:
    """
    Update a post's caption and associated images.

    This function handles partial updates to a post, including caption
    modification and image management. It supports adding new images,
    deleting existing images by ID, and enforces a maximum limit of 10
    images per post.

    The update process includes validation for post existence, ownership
    authorization, and image count constraints before applying changes.

    Args:
        db (AsyncSession): Asynchronous database session used for
            persistence operations.
        post (Post): The post instance to be updated.
        user_id (int): ID of the user performing the update (used for
            ownership validation).
        caption (str | None): Updated caption for the post.
        new_images (list): List of new image URLs to add.
        images_to_delete (list[int]): List of image IDs to remove
            from the post.

    Returns:
        Post | None: The updated post instance if successful.
    """

    try:
        if images_to_delete:
            await _delete_post_images(post, images_to_delete, db)

        if new_images and len(new_images) > 0:
            await _add_post_images(post, new_images, db)

        if caption is not None:
            post.caption = caption

        await db.commit()
        await db.refresh(post)

        return post

    except Exception:
        await db.rollback()
        raise
