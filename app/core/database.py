"""
Database configuration and session management.
"""
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from supabase import create_client, Client
import logging

from sqlalchemy import text

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Global variables for lazy initialization
engine: Optional[object] = None
AsyncSessionLocal: Optional[object] = None
supabase: Optional[Client] = None


def get_engine():
    """Get or create the database engine."""
    global engine
    if engine is None:
        if not settings.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            future=True
        )
    return engine


def get_session_factory():
    """Get or create the session factory."""
    global AsyncSessionLocal
    if AsyncSessionLocal is None:
        AsyncSessionLocal = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False
        )
    return AsyncSessionLocal


def get_supabase_client():
    """Get or create the Supabase client."""
    global supabase
    if supabase is None:
        if not settings.supabase_url or not settings.supabase_key:
            logger.warning("Supabase credentials not configured. Some features may not work.")
            return None
        supabase = create_client(settings.supabase_url, settings.supabase_key)
    return supabase


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    Creates btree_gist extension required for EXCLUDE constraints.
    """
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            # Enable btree_gist extension for EXCLUDE constraints with mixed operators
            # This is required for combining = and && operators in the booking overlap constraint
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
            
            # Import all models to ensure they are registered
            from app.models import user, classroom, booking  # noqa
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully with btree_gist extension")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

