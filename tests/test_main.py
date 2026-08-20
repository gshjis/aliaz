"""Тесты для API приложения."""

import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture
async def test_client():
    """Тестовый клиент для тестов."""
    from config.settings import Settings
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address

    from api.auth import router as auth_router
    from api.words import router as words_router

    test_settings = Settings()
    test_app = FastAPI(
        title=test_settings.app_name,
        version=test_settings.app_version,
        debug=test_settings.debug,
    )

    # CORS middleware
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=test_settings.allowed_origins or test_settings.allowed_hosts,
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

    # Корневой эндпоинт
    @test_app.get("/")
    async def root() -> dict[str, str]:
        """Корневой эндпоинт для проверки работоспособности."""
        return {"status": "ok", "message": f"Welcome to {test_settings.app_name} API"}

    from fastapi.testclient import TestClient
    return TestClient(test_app)


def test_root(test_client) -> None:
    """Тест корневого эндпоинта."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Welcome to aliaz API"}
