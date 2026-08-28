import logging
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from .config import settings

logger = logging.getLogger("connect_hub.database")


class Base(AsyncAttrs, DeclarativeBase):
    """Base model class with async attribute support for SQLAlchemy 2.0."""
    pass


def get_normalized_db_url(raw_url: str) -> str:
    """Normalize database connection string to use async drivers."""
    if not raw_url:
        return "sqlite+aiosqlite:///./connect_hub.db"
    
    url = raw_url.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("mysql://") and not url.startswith("mysql+aiomysql://"):
        url = url.replace("mysql://", "mysql+aiomysql://", 1)
    elif url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
        url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        
    return url


# Initialize async SQLAlchemy engine
normalized_url = get_normalized_db_url(settings.DATABASE_URL)
engine_kwargs = {"echo": False, "future": True}

if normalized_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

async_engine: AsyncEngine = create_async_engine(normalized_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Optional MongoDB Client Support
mongo_client = None
mongo_db = None

if settings.MONGODB_URI:
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_client = AsyncIOMotorClient(settings.MONGODB_URI)
        mongo_db = mongo_client[settings.MONGODB_DB_NAME]
        logger.info(f"Connected to MongoDB at {settings.MONGODB_URI}")
    except Exception as e:
        logger.warning(f"Failed to initialize MongoDB client: {e}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized successfully.")
