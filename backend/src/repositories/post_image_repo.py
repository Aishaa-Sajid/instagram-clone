import asyncio
from src.services.cloudinary_service import delete_image_from_cloudinary
from src.database.models.post import Post
from src.database.models.post_image import PostImage
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger


async def delete_post_images(
    post: Post, image_ids: list[int], db: AsyncSession
) -> None:
    """
    Delete specified images associated with a post.

    Removes images from a post whose IDs match the provided list.
    Also triggers asynchronous deletion from Cloudinary for images
    that have a `public_id`. The post's image relationship is updated
    to retain only the remaining images.

    Args:
        post: The post instance containing related images.
        image_ids: List of image IDs to be deleted.
        db: The asynchronous database session used for persistence.

    Returns:
        None
    """
    if not image_ids:
        return

    image_ids = set(image_ids)
    remaining = []
    delete_tasks = []

    for img in post.images:
        if img.id in image_ids:
            if img.public_id:
                delete_tasks.append(delete_image_from_cloudinary(img.public_id))
        else:
            remaining.append(img)

    results = []
    if delete_tasks:
        results = (
            await asyncio.gather(*delete_tasks, return_exceptions=True)
            if delete_tasks
            else []
        )

    post.images = remaining

    for r in results:
        if isinstance(r, Exception):
            logger.error(f"Cloudinary delete failed: {r}")


async def add_post_images(post: Post, images: list[PostImage], db: AsyncSession):
    """
    Associate new images with a post.

    Creates new PostImage records and links them to the given post.
    Each image is persisted in the database and associated via
    `post_id`.

    Args:
        post: The post instance to which images will be added.
        images: List of image objects containing image_url and public_id.

    Returns:
        None
    """
    db_images = [
        PostImage(post_id=post.id, image_url=img.image_url, public_id=img.public_id)
        for img in images
    ]

    db.add_all(db_images)
