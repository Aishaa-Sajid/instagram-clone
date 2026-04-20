import cloudinary.uploader
import src.services.Cloudinary.cloudinary_config
from fastapi import UploadFile
import io


async def upload_image(file: UploadFile, folder: str = "profile_pics") -> str:

    file_bytes = await file.read()
    file_obj = io.BytesIO(file_bytes)

    result = cloudinary.uploader.upload(
        file_obj, folder=folder  
    )

    return result["secure_url"]
