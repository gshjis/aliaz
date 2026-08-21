"""Главная точка входа приложения FastAPI."""

import logging
import time

from config.settings import settings
from database.connection import engine
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.auth import router as auth_router
from api.words import router as words_router

# Rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins or settings.allowed_hosts,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(words_router, prefix="/api/v1")

logger = logging.getLogger(__name__)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логировать входящие запросы."""
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    logger.debug(
        f"{request.method} {request.url.path} -> {response.status_code} ({process_time:.2f}ms)"
    )
    return response


@app.get("/")
async def root() -> dict[str, str]:
    """Корневой эндпоинт для проверки работоспособности."""
    return {"status": "ok", "message": f"Welcome to {settings.app_name} API"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Эндпоинт для healthcheck: проверка работоспособности сервиса."""
    return {"status": "ok", "message": "healthy"}


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Закрыть соединения с БД при graceful shutdown."""
    logger.info("Shutting down database connections...")
    await engine.dispose()
    logger.info("Database connections closed")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
