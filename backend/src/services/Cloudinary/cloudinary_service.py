import cloudinary.uploader
import src.services.cloudinary.cloudinary_config
from fastapi import UploadFile
import io
import asyncio
from cloudinary.uploader import destroy
from src.schemas.post_image import PostUploadImage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.models.post_image import PostImage


async def upload_image(file: UploadFile, folder: str = "uploads") -> PostUploadImage:
    """
    Upload image to Cloudinary asynchronously.
    Can be used for:
    - profile images
    - post images
    - any media uploads
    """

    file_bytes = await file.read()
    file_obj = io.BytesIO(file_bytes)

    result = await asyncio.to_thread(
        cloudinary.uploader.upload, file_obj, folder=folder
    )
    print(result)
    if not result.get("public_id"):
        raise Exception("Cloudinary did not return public_id")
    return PostUploadImage(url=result["secure_url"], public_id=result["public_id"])


async def delete_image_from_cloudinary(public_id: str):
    try:
        result = await asyncio.to_thread(cloudinary.uploader.destroy, public_id)

        if result.get("result") != "ok":
            raise Exception(f"Cloudinary delete failed: {result}")

        return result

    except Exception as e:
        print(f"Cloudinary delete failed: {e}")
        return None
