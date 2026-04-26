from src.services.cloudinary.cloudinary_service import delete_image_from_cloudinary
from src.database.models.post import Post
from src.database.models.post_image import PostImage
from sqlalchemy.ext.asyncio import AsyncSession

async def _delete_post_images(post: Post, image_ids: list[int], db: AsyncSession):
    
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
            await delete_image_from_cloudinary(img.public_id)
        else:
            remaining.append(img)

    post.images = remaining

    # async def _delete_post_images(post: Post, image_ids: list[int], db: AsyncSession):
    #     for img in list(post.images):
    #         if img.id in image_ids:
    #             await delete_image_from_cloudinary(img.public_id)  # external cleanup
    # post.images = [img for img in post.images if img.id not in image_ids]  # ORM cascade handles DB


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
        PostImage(
            post_id=post.id,
            image_url=img.image_url,
            public_id=img.public_id
        )
        for img in images
    ]

    db.add_all(db_images)
    # post.images.extend(images)
   