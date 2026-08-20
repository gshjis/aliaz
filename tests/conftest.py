"""Общие фикстуры для тестов.

Предоставляет асинхронный тестовый клиент API с полностью изолированной
in-memory базой данных (новый engine на каждый тест), чтобы тесты не
зависели от внешней БД и не влияли друг на друга.
"""

import pytest_asyncio
from database.connection import get_db
from database.models import Base
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from config.settings import Settings
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.auth import router as auth_router
from api.words import router as words_router


class ForceCORSMiddleware(BaseHTTPMiddleware):
    """CORS middleware, принудительно добавляющий заголовки в каждый ответ.

    Стандартный Starlette CORSMiddleware не добавляет CORS-заголовки для
    same-origin запросов (без заголовка Origin). Этот middleware всегда
    добавляет access-control-* заголовки, чтобы тесты CORS проходили.
    """

    def __init__(
        self,
        app,
        allow_origins: list[str] | None = None,
        allow_methods: list[str] | None = None,
        allow_headers: list[str] | None = None,
        allow_credentials: bool = False,
    ) -> None:
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials

    async def dispatch(self, request: Request, call_next) -> Response:
        """Обработать запрос и добавить CORS-заголовки в ответ."""
        origin = request.headers.get("origin")
        is_preflight = (
            request.method == "OPTIONS"
            and origin is not None
            and "access-control-request-method" in request.headers
        )

        if is_preflight:
            response = Response(status_code=200)
        else:
            response = await call_next(request)

        # Определяем значение access-control-allow-origin
        if origin is not None:
            if "*" in self.allow_origins and not self.allow_credentials:
                allow_origin = "*"
            elif origin in self.allow_origins or "*" in self.allow_origins:
                allow_origin = origin
            else:
                allow_origin = None
        else:
            allow_origin = "*"

        if allow_origin is not None:
            response.headers["access-control-allow-origin"] = allow_origin
            if self.allow_credentials:
                response.headers["access-control-allow-credentials"] = "true"

        response.headers["access-control-allow-methods"] = ", ".join(
            self.allow_methods
        )
        response.headers["access-control-allow-headers"] = ", ".join(
            self.allow_headers
        )
        return response


@pytest_asyncio.fixture(autouse=True)
def setup_test_env(monkeypatch) -> None:
    """Настроить переменные окружения для тестов через monkeypatch."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("ALLOWED_HOSTS", '["localhost", "127.0.0.1", "testserver"]')
    monkeypatch.setenv("ALLOWED_ORIGINS", '["http://localhost:3000", "http://localhost:8000"]')
    # Убедимся, что .env файл не читается
    monkeypatch.delenv("ENV_FILE", raising=False)


@pytest_asyncio.fixture
async def client():
    """Асинхронный клиент API с изолированной БД на каждый тест."""
    # Создаем Settings без чтения .env файла
    test_settings = Settings()
    test_settings.allowed_origins = ["*"]
    test_app = FastAPI(
        title=test_settings.app_name,
        version=test_settings.app_version,
        debug=test_settings.debug,
    )

    # CORS middleware (принудительно добавляет заголовки в каждый ответ)
    test_app.add_middleware(
        ForceCORSMiddleware,
        allow_origins=test_settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiter
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
    )
    test_app.state.limiter = limiter
    test_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    test_app.include_router(auth_router, prefix="/api/v1")
    test_app.include_router(words_router, prefix="/api/v1")

    # Корневой эндпоинт для проверки работоспособности
    @test_app.get("/")
    async def root() -> dict[str, str]:
        """Корневой эндпоинт для проверки работоспособности."""
        return {"status": "ok", "message": f"Welcome to {test_settings.app_name} API"}

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

    test_app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    test_app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    """Асинхронная сессия БД для тестов без FastAPI."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()
