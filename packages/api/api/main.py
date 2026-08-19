"""Главная точка входа приложения FastAPI."""

from config.settings import settings
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from api.auth import router as auth_router
from api.words import router as words_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(words_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Корневой эндпоинт для проверки работоспособности."""
    return {"status": "ok", "message": f"Welcome to {settings.app_name} API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
