import asyncio
from src.services.cloudinary.cloudinary_service import delete_image_from_cloudinary
from src.database.models.post import Post
from src.database.models.post_image import PostImage
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger


async def _delete_post_images(
    post: Post, image_ids: list[int], db: AsyncSession
) -> None:
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


async def _add_post_images(post: Post, images: list[PostImage], db: AsyncSession):
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
    db_images = [
        PostImage(post_id=post.id, image_url=img.image_url, public_id=img.public_id)
        for img in images
    ]

    db.add_all(db_images)
