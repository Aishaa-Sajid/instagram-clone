import cloudinary.uploader
import src.services.Cloudinary.cloudinary_config
from fastapi import UploadFile
import io
import asyncio


async def upload_image(file: UploadFile, folder: str = "uploads") -> str:
    """
    Upload image to Cloudinary asynchronously.
    Can be used for:
    - profile images
    - post images
    - any media uploads
    """

    file_bytes = await file.read()

    result = await asyncio.to_thread(
        cloudinary.uploader.upload, file_bytes, folder=folder
    )

    return result["secure_url"]


def delete_image(public_id: str):
    """
    Delete image from Cloudinary using its public ID.
    """
    result = cloudinary.uploader.destroy(public_id)
    return result
