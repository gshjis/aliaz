"""Главная точка входа приложения FastAPI."""

from api.auth import router as auth_router
from api.words import router as words_router
from config.settings import settings
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["gshjis.com"])
app.include_router(auth_router)
app.include_router(words_router)


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
