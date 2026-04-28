from fastapi import HTTPException, UploadFile
from src.core.constants import (
    MAX_IMAGES,
    ALLOWED_CONTENT_TYPES,
    MAX_FILE_SIZE,
)


async def validate_files(files: list[UploadFile]):
    if len(files) > MAX_IMAGES:
        raise HTTPException(400, f"Max {MAX_IMAGES} images allowed")

    for file in files:
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                400,
                f"{file.filename} has invalid type {file.content_type}",
            )

        contents = await file.read()

        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                400,
                f"{file.filename} exceeds max size of 5MB",
            )

        await file.seek(0)  # reset pointer
