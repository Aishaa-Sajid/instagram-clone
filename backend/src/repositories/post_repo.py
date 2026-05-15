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


async def get_post_by_user_id(db: AsyncSession, post_id: int) -> Post | None:
    stmt = (
        select(Post)
        .options(
            selectinload(Post.owner),
            selectinload(Post.images),
            selectinload(Post.likes),
        )
        .where(Post.id == post_id)
        .joins(
            Follow,
        )
    )

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def build_post_query(viewer_id: int):
    """
    Build a reusable SQLAlchemy query for retrieving posts.

    This query applies post visibility rules based on account privacy
    and follower relationship status. It also includes additional
    metadata required for post responses such as likes count,
    comments count, and whether the viewer has liked the post.

    Included features:
        - Privacy access control
        - Likes count aggregation
        - Comments count aggregation
        - "is_liked" flag for the viewer
        - Owner relationship eager loading
        - Post images eager loading

    Visibility rules:
        - Public account posts are visible to everyone.
        - Users can always view their own posts.
        - Private account posts are visible only to accepted followers.

    Args:
        viewer_id (int):
            ID of the authenticated user requesting posts.

    Returns:
        Select:
            SQLAlchemy select statement containing:
                - Post object
                - likes_count
                - comments_count
                - is_liked flag
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
            func.coalesce(likes_subquery.c.likes_count,0,).label("likes_count"),
            func.coalesce(comments_subquery.c.comments_count,0,).label("comments_count"),
            is_liked_expr,
        )
        .join(User, User.id == Post.user_id)
        .outerjoin(likes_subquery,Post.id == likes_subquery.c.post_id,)
        .outerjoin(comments_subquery,Post.id == comments_subquery.c.post_id,)
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

    This function fetches posts while enforcing account privacy rules.
    It supports pagination, optional caption search, and filtering
    posts by a specific user.

    Visibility rules:
        - Public account posts are visible to everyone.
        - Users can always view their own posts.
        - Private account posts are visible only to accepted followers.
        - Pending or rejected follow requests do not grant access.

    Additional response data:
        - Total likes count
        - Total comments count
        - Whether the authenticated user liked the post

    Args:
        db (AsyncSession):
            Asynchronous database session.

        limit (int):
            Maximum number of posts to return.

        skip (int):
            Number of posts to skip for pagination.

        viewer_id (int):
            ID of the authenticated user requesting posts.

        search (str | None, optional):
            Optional caption search keyword.

        target_user_id (int | None, optional):
            Filter posts belonging to a specific user.

    Returns:
        list[PostResponse]:
            List of accessible posts with aggregated metadata.
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
) -> PostResponse | None:
    """
    Retrieve a single accessible post by ID.

    This function fetches a post while enforcing account privacy
    and visibility rules. It also includes likes count,
    comments count, and the "is_liked" status for the requesting user.

    Visibility rules:
        - Public account posts are visible to everyone.
        - Users can always view their own posts.
        - Private account posts are visible only to accepted followers.

    Args:
        db (AsyncSession):
            Asynchronous database session.

        post_id (int):
            ID of the target post.

        current_user_id (int):
            ID of the authenticated user requesting the post.

    Returns:
        PostResponse | None:
            Serialized post response if accessible.
    """
    stmt = build_post_query(current_user_id).where(Post.id == post_id)

    result = await db.execute(stmt)

    row = result.first()

    if not row:
        raise Exception("Post not found or inaccessible")

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
    for img in post.images:
        if img.public_id:
            await delete_image_from_cloudinary(img.public_id)

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
        caption (str | None): Updated caption for the post.
        new_images (list): List of new image URLs to add.
        images_to_delete (list[int]): List of image IDs to remove
            from the post.

    Returns:
        Post | None: The updated post instance if successful.
    """
    try:
        if images_to_delete:
            await delete_post_images(post, images_to_delete, db)

        if new_images:
            await add_post_images(post, new_images, db)

        if caption is not None:
            post.caption = caption

        await db.commit()
        await db.refresh(post)

        return post

    except Exception as e:
        await db.rollback()
        raise Exception(f"Failed to update post: {str(e)}")
