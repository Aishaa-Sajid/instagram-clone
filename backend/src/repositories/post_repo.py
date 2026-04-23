from fastapi import HTTPException, Response, status
from sqlalchemy import select, func
from sqlalchemy.ext import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.services.Cloudinary.cloudinary_service import upload_image
from src.database.models.post_image import PostImage
from src.schemas.post import PostCreate, PostResponse


from src.database.models.post import Post


async def get_post_by_id(db: AsyncSession, post_id: int) -> Post | None:
    stmt = (
        select(Post)
        .options(selectinload(Post.owner), selectinload(Post.images))
        .where(Post.id == post_id)
    )

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_posts(
    db: AsyncSession, limit: int, skip: int, search: str | None = None
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
        .options(selectinload(Post.owner), selectinload(Post.images))
        .limit(limit)
        .offset(skip)
    )

    if search:
        stmt = stmt.where(Post.caption.ilike(f"%{search}%"))

    result = await db.execute(stmt)
    return result.scalars().all()


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

    return result.scalar_one()


async def get_post(db: AsyncSession, post_id: int) -> Post | None:
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

    return post


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


async def _delete_images(post: Post, image_ids: list[int], db: AsyncSession):
    """
     Remove specified images associated with a post.

    This function iterates through the images linked to the given post
    and deletes those whose IDs match the provided list. The post's
    image relationship is updated to retain only the remaining images.

    Args:
        post (Post): The post instance containing related images.
        image_ids (list[int]): List of image IDs to be deleted.
        db (AsyncSession): Asynchronous database session used to
            perform delete operations.

    Returns:
        None
    """

    remaining = []

    for img in post.images:
        if img.id in image_ids:
            await db.delete(img)
        else:
            remaining.append(img)

    post.images = remaining


async def _add_images(post: Post, images: list[PostImage]):
    """Associate new images with a post.

    This function links each provided image to the given post by setting
    the relationship on both sides. The images are then added to the
    post's image collection.

    Args:
        post (Post): The post instance to which the images will be added.
        images (list[PostImage]): List of image instances to associate
            with the post.

    Returns:
        None
    """
    for img in images:
        img.post = post
    post.images.extend(images)


async def update_post_repo(
    db: AsyncSession,
    post_id: int,
    user_id: int,
    caption: str | None = None,
    new_images: list[PostImage] | None = None,
    images_to_delete: list[int] | None = None,
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
        post_id (int): ID of the post to be updated.
        user_id (int): ID of the user performing the update (used for
            ownership validation).
        caption (str | None): Optional new caption for the post.
        new_images (list[PostImage] | None): List of new images to be
            added to the post.
        images_to_delete (list[int] | None): List of image IDs to remove
            from the post.

    Returns:
        Post | None: The updated post instance if successful.
    """
    post = await get_post_by_id(db, post_id)

    if not post:
        raise Exception("Post not found")

    if post.user_id != user_id:
        raise Exception("Not allowed")

    new_images = new_images or []
    images_to_delete = images_to_delete or []

    remaining_count = [img for img in post.images if img.id not in images_to_delete]

    if len(remaining_count) + len(new_images) > 10:
        raise Exception("A post can have maximum 10 images")

    if images_to_delete:
        await _delete_images(post, images_to_delete, db)

    if new_images:
        await _add_images(post, new_images)

    if caption is not None:
        post.caption = caption

    await db.commit()
    await db.refresh(post)

    return post
