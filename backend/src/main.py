from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import auth_api, user_api, post_api, health_check_api, like_api,comment_api,story_api,search_api,follow_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("App starting...")

    yield  # app runs here

    # Shutdown logic
    print("App shutting down...")


# Initialize the FastAPI app
app = FastAPI(title="Blog Post", version="1.0.0", lifespan=lifespan)

# allow cors
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