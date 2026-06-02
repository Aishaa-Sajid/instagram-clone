from fastapi import Request, status
from fastapi.responses import JSONResponse
from src.core.exceptions import AppError
from loguru import logger



async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
        },
    )

async def global_exception_handler(request: Request, exc: Exception):
    """
    Handles ONLY unexpected system errors.
    Domain errors (AppError) are handled in route layer.
    """

    logger.exception("Unhandled exception occurred")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
        },
    )