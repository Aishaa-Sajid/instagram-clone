from src.database.models.follow import Follow
from src.database.models.user import User
from src.utils.enum import FollowStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.database.models.like import Like
from src.database.models.comment import Comment
from src.services.cloudinary_service import delete_image_from_cloudinary
from src.database.models.post_image import PostImage
from src.schemas.post import PostCreate, PostResponse
from src.utils.constants import MAX_IMAGES
from src.database.models.post import Post
from src.repositories.post_image_repo import add_post_images, delete_post_images
from sqlalchemy import select, func, exists, or_
from src.core.exceptions import TooManyImagesError, PostNotFoundError
from loguru import logger

async def get_post_by_id(db: AsyncSession, post_id: int) -> Post:
    """
    Retrieve a post by its ID with related data.

    Loads the post along with its owner, images, and likes using eager
    loading. Raises an exception if the post does not exist.

    Args:
        db: The asynchronous SQLAlchemy database session.
        post_id: ID of the post to retrieve.

    Returns:
        The Post ORM instance.

    Raises:
        PostNotFoundError: If the post does not exist.
    """
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
    post= result.scalar_one_or_none()
    
    if not post:
        raise PostNotFoundError("Post not found")
    
    return post


def build_post_query(viewer_id: int):
    """
    Build a SQLAlchemy query for retrieving posts with visibility rules.

    This query applies:
        - Account privacy rules
        - Follow-based access control
        - Aggregated like and comment counts
        - "is_liked" flag for the viewer
        - Eager loading for owner and images

    Visibility rules:
        - Public posts are visible to everyone.
        - Users can always view their own posts.
        - Private posts are visible only to accepted followers.

    Args:
        viewer_id: ID of the authenticated user requesting posts.

    Returns:
        SQLAlchemy Select object for post retrieval.
    """

    is_accepted_follower = exists().where(
        Follow.following_id == Post.user_id,
        Follow.follower_id == viewer_id,
        Follow.status == FollowStatus.ACCEPTED,
    )

    access_filter = or_(
        User.is_private.is_(False), Post.user_id == viewer_id, is_accepted_follower
    )

    likes_subquery = (
        select(
            Like.post_id,
            func.count(Like.id).label("likes_count"),
        )
        .group_by(Like.post_id)
        .subquery()
    )

    comments_subquery = (
        select(
            Comment.post_id,
            func.count(Comment.id).label("comments_count"),
        )
        .group_by(Comment.post_id)
        .subquery()
    )

    is_liked_expr = (
        exists()
        .where(
            Like.post_id == Post.id,
            Like.user_id == viewer_id,
        )
        .label("is_liked")
    )

    stmt = (
        select(
            Post,
            func.coalesce(
                likes_subquery.c.likes_count,
                0,
            ).label("likes_count"),
            func.coalesce(
                comments_subquery.c.comments_count,
                0,
            ).label("comments_count"),
            is_liked_expr,
        )
        .join(User, User.id == Post.user_id)
        .outerjoin(
            likes_subquery,
            Post.id == likes_subquery.c.post_id,
        )
        .outerjoin(
            comments_subquery,
            Post.id == comments_subquery.c.post_id,
        )
        .where(access_filter)
        .options(
            selectinload(Post.owner),
            selectinload(Post.images),
        )
    )

    return stmt


async def get_posts(
    db: AsyncSession,
    *,
    limit: int,
    skip: int,
    viewer_id: int,
    search: str | None = None,
    target_user_id: int | None = None,
) -> list[PostResponse]:
    """
    Retrieve posts accessible to the authenticated user.

    Supports:
        - Pagination
        - Caption search filtering
        - Filtering by specific user
        - Privacy-based access control

    Each post includes:
        - Likes count
        - Comments count
        - Whether the viewer liked the post

    Args:
        db: The asynchronous database session.
        limit: Maximum number of posts to return.
        skip: Number of posts to skip for pagination.
        viewer_id: ID of the authenticated user.
        search: Optional caption search keyword.
        target_user_id: Optional filter for a specific user.

    Returns:
        List of PostResponse objects.
    """

    stmt = build_post_query(viewer_id)

    if target_user_id is not None:
        stmt = stmt.where(Post.user_id == target_user_id)

    if search:
        stmt = stmt.where(Post.caption.ilike(f"%{search}%"))

    stmt = stmt.order_by(Post.created_at.desc()).limit(limit).offset(skip)
    result = await db.execute(stmt)

    rows = result.all()

    posts: list[PostResponse] = []

    for post, likes_count, comments_count, is_liked in rows:
        posts.append(
            PostResponse(
                id=post.id,
                caption=post.caption,
                created_at=post.created_at,
                updated_at=post.updated_at,
                user_id=post.user_id,
                owner=post.owner,
                images=post.images,
                likes_count=likes_count,
                comments_count=comments_count,
                is_liked=is_liked,
            )
        )

    return posts


async def create_post(db: AsyncSession, post: PostCreate, user_id: int) -> Post:
    """
    Create a new post with associated images.

    Inserts a post for the given user and attaches images to it.
    Enforces maximum image limit defined by MAX_IMAGES.

    Args:
        db: The asynchronous database session.
        post: Post creation payload containing caption and images.
        user_id: ID of the user creating the post.

    Returns:
        The created Post ORM instance with owner and images loaded.

    Raises:
        TooManyImagesError: If image count exceeds allowed limit.
    """
    if len(post.images) > MAX_IMAGES:
        raise TooManyImagesError(f"A post can have maximum {MAX_IMAGES} images")

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

    result = await db.execute(
        select(Post)
        .options(selectinload(Post.images), selectinload(Post.owner))
        .where(Post.id == new_post.id)
    )

    return result.scalar_one()


async def get_post(
    db: AsyncSession, post_id: int, current_user_id: int
) -> PostResponse:
    """
    Retrieve a single post by ID with access control.

    Enforces privacy rules and returns post metadata including:
        - Likes count
        - Comments count
        - Viewer like status

    Args:
        db: The asynchronous database session.
        post_id: ID of the post.
        current_user_id: ID of the requesting user.

    Returns:
        PostResponse containing full post data.

    Raises:
        PostNotFoundError: If post does not exist or is inaccessible.
    """
    stmt = build_post_query(current_user_id).where(Post.id == post_id)

    result = await db.execute(stmt)

    row = result.first()

    if not row:
        raise PostNotFoundError("Post not found or inaccessible")

    post, likes_count, comments_count, is_liked = row

    return PostResponse(
        id=post.id,
        caption=post.caption,
        created_at=post.created_at,
        updated_at=post.updated_at,
        user_id=post.user_id,
        owner=post.owner,
        images=post.images,
        likes_count=likes_count,
        comments_count=comments_count,
        is_liked=is_liked,
    )


async def delete_post(db: AsyncSession, post: Post):
    """
    Delete a post and its associated images from external storage.

    Removes all post images from Cloudinary before deleting the post
    from the database.

    Args:
        db: The asynchronous database session.
        post: The post instance to delete.

    Returns:
        None
    """
    for img in post.images:
        if img.public_id:
            try:
                await delete_image_from_cloudinary(img.public_id)
            except Exception:
                logger.exception(f"Failed to delete image from Cloudinary: {img.public_id}")

    await db.delete(post)
    
    await db.commit()


async def update_post_repo(
    db: AsyncSession,
    post: Post,
    caption: str | None,
    new_images: list,
    images_to_delete: list[int],
) -> Post:
    """
    Update a post's caption and images.

    Supports partial updates:
        - Updating caption
        - Adding new images
        - Deleting existing images

    Enforces image constraints via repository helpers.

    Args:
        db: The asynchronous database session.
        post: The post instance to update.
        caption: Updated caption (if any).
        new_images: List of new images to add.
        images_to_delete: List of image IDs to remove.

    Returns:
        The updated Post ORM instance.
    """

    if images_to_delete:
        await delete_post_images(post, images_to_delete, db)

    if new_images:
        await add_post_images(post, new_images, db)

    if caption is not None:
        post.caption = caption
    
    await db.commit()
   
    await db.refresh(post)
    return post


