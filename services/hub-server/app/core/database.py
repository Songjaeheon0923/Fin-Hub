"""
Database setup and connection management for Hub Server
"""

import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from sqlalchemy.orm import DeclarativeBase

from .config import get_config

logger = logging.getLogger(__name__)

# Database metadata and base class
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)


class Base(DeclarativeBase):
    """Base class for all database models"""
    metadata = metadata


# Global database engine and session maker
_engine: AsyncEngine = None
_async_session_maker: async_sessionmaker = None


def create_engine() -> AsyncEngine:
    """Create database engine"""
    config = get_config()

    engine = create_async_engine(
        config.database_url,
        echo=config.debug,
        pool_size=config.db_pool_size,
        pool_pre_ping=True,
        pool_recycle=3600,  # Recycle connections every hour
        future=True
    )

    logger.info(f"Database engine created for {config.database_url}")
    return engine


def get_engine() -> AsyncEngine:
    """Get global database engine"""
    global _engine
    if _engine is None:
        _engine = create_engine()
    return _engine


def get_session_maker() -> async_sessionmaker:
    """Get async session maker"""
    global _async_session_maker
    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    return _async_session_maker


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with automatic cleanup"""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_session_dependency() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions"""
    async with get_session() as session:
        yield session


async def init_database():
    """Initialize database tables"""
    engine = get_engine()

    try:
        # Import all models to ensure they're registered with Base.metadata
        from ..models import registry, tools

        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database tables created successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_database():
    """Close database connections"""
    global _engine, _async_session_maker

    if _engine:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
        logger.info("Database connections closed")


# Health check function
async def check_database_health() -> bool:
    """Check database connectivity"""
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False