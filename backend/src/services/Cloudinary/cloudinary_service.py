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
    file_obj = io.BytesIO(file_bytes)

    result = await asyncio.to_thread(
        cloudinary.uploader.upload,
        file_bytes,
        folder=folder
    )

    return result["secure_url"]
