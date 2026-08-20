"""Асинхронное подключение к базе данных."""

import logging
from collections.abc import AsyncGenerator

from config import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    engine = create_async_engine(settings.database_url, echo=settings.debug)
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    try:
        async with async_session_factory() as session:
            yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise


async def init_db() -> None:
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
