import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import init_db
from app.middlewares.cors import setup_cors
from app.middlewares.error_handler import setup_error_handlers
from app.modules.auth.routes import router as auth_router
from app.modules.users.routes import router as users_router
from app.modules.posts.routes import router as posts_router
from app.modules.stories.routes import router as stories_router
from app.modules.groups.routes import router as groups_router
from app.modules.chat.routes import router as chat_router
from app.modules.calls.routes import router as calls_router
from app.modules.notifications.routes import router as notifications_router
from app.modules.media.routes import router as media_router
from app.modules.events.routes import router as events_router
from app.modules.support.routes import router as support_router
from app.modules.settings.routes import router as settings_router
from app.modules.friends.routes import router as friends_router

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("connect_hub")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database & Uploads Directory
    logger.info("Initializing database schema...")
    await init_db()
    os.makedirs(settings.LOCAL_UPLOAD_DIR, exist_ok=True)
    logger.info(f"Connect-Hub API started in {settings.APP_ENV} mode.")
    yield
    # Shutdown
    logger.info("Connect-Hub API shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Full Modular MVC Backend API for Connect-Hub Social, Stories, Groups, Realtime Chat & WebRTC PeerJS Calling",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup Middlewares
setup_cors(app)
setup_error_handlers(app)

# Mount Local Static Uploads
os.makedirs(settings.LOCAL_UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.LOCAL_UPLOAD_DIR), name="uploads")

# Mount API V1 Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(posts_router, prefix=settings.API_V1_STR)
app.include_router(stories_router, prefix=settings.API_V1_STR)
app.include_router(groups_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(notifications_router, prefix=settings.API_V1_STR)
app.include_router(media_router, prefix=settings.API_V1_STR)
app.include_router(events_router, prefix=settings.API_V1_STR)
app.include_router(support_router, prefix=settings.API_V1_STR)
app.include_router(settings_router, prefix=settings.API_V1_STR)
app.include_router(friends_router, prefix=settings.API_V1_STR)

# Mount Calls & PeerJS Routers (handles /api/v1/calls and /peerjs signaling protocol)
app.include_router(calls_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "environment": settings.APP_ENV,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "database": "connected"}
