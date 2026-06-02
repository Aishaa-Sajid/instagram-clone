from fastapi import UploadFile
from src.core.exceptions import TooManyImagesError, UnsupportedFileTypeError
from src.utils.constants import (
    MAX_IMAGES,
    ALLOWED_CONTENT_TYPES,
    MAX_FILE_SIZE,
    ALLOWED_EXTENSIONS,
)
from pathlib import Path


async def validate_files(files: UploadFile | list[UploadFile]):

    if not isinstance(files, list):
        files = [files]

    if len(files) > MAX_IMAGES:
        raise TooManyImagesError(f"Max {MAX_IMAGES} images allowed")

    for file in files:

        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise UnsupportedFileTypeError(f"{file.filename} has invalid type {file.content_type}")

        ext = Path(file.filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError(f"{file.filename} has invalid extension {ext}")

        content = await file.read()
        await file.seek(0)

        if len(content) > MAX_FILE_SIZE:
            raise TooManyImagesError(f"{file.filename} exceeds max size of {MAX_FILE_SIZE} bytes")
        await file.seek(0)

