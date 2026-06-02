import cloudinary.uploader
from fastapi import UploadFile
import io
import asyncio
from src.schemas.post_image import PostUploadImage
from src.core.exceptions import ExternalServiceError
import cloudinary
from src.database.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

async def upload_image(file: UploadFile, folder: str = "uploads") -> PostUploadImage:
    """
    Upload image to Cloudinary asynchronously.
    Can be used for:
    - profile images
    - post images
    - any media uploads
    """
    await file.seek(0)
    file_bytes = await file.read()
    file_obj = io.BytesIO(file_bytes)

    try:
        result = await asyncio.to_thread(
            cloudinary.uploader.upload, file_obj, folder=folder
        )
    
        if not result.get("public_id"):
            raise ExternalServiceError(
                "Cloudinary did not return public_id"
            )
        return PostUploadImage(url=result["secure_url"], public_id=result["public_id"])

    except Exception:
        raise ExternalServiceError(
            "Image upload failed"
        )

async def delete_image_from_cloudinary(public_id: str):

    try:
        result = await asyncio.to_thread(cloudinary.uploader.destroy, public_id)
        if result.get("result") != "ok":
            raise ExternalServiceError(f"Cloudinary delete failed: {result}")

        return result
    
    except Exception as e:
        raise ExternalServiceError(f"Cloudinary delete failed: {str(e)}")
