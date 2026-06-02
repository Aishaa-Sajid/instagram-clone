from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import (
    auth_api,
    user_api,
    post_api,
    health_check_api,
    like_api,
    comment_api,
    story_api,
    search_api,
    follow_api,
)
from src.core.exceptions import AppError
from src.core.exception_handler import global_exception_handler, app_error_handler
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("App starting...")

    yield  # app runs here

    # Shutdown logic
    logger.info("App shutting down...")


app = FastAPI(title="Instagram Clone", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=health_check_api.router, prefix="/health")
app.include_router(router=auth_api.router, prefix="/auth")
app.include_router(router=user_api.router, prefix="/users")
app.include_router(router=post_api.router, prefix="/posts")
app.include_router(router=like_api.router, prefix="/likes")
app.include_router(router=comment_api.router, prefix="/comments")
app.include_router(router=story_api.router, prefix="/stories")
app.include_router(router=search_api.router, prefix="/search")
app.include_router(router=follow_api.router, prefix="/follow")

app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(AppError, app_error_handler)
