"""Общие фикстуры для тестов.

Предоставляет асинхронный тестовый клиент API с полностью изолированной
in-memory базой данных (новый engine на каждый тест), чтобы тесты не
зависели от внешней БД и не влияли друг на друга.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ["ALLOWED_HOSTS"] = '["localhost", "127.0.0.1", "testserver"]'

import pytest_asyncio
from api.main import app
from database.connection import get_db
from database.models import Base
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool


@pytest_asyncio.fixture
async def client():
    """Асинхронный клиент API с изолированной БД на каждый тест."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()
