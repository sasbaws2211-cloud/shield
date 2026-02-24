"""Async database configuration and session management."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """Dependency for getting async database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables asynchronously."""
    async with engine.begin() as conn:
        # Drop all tables if in development
        if settings.debug:
            await conn.run_sync(SQLModel.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(SQLModel.metadata.create_all)
    
    logger.info("Database tables initialized")


async def close_db() -> None:
    """Close database connection."""
    await engine.dispose()
    logger.info("Database connection closed")
