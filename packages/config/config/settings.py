"""Глобальная конфигурация проекта."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки из переменных окружения и файла .env."""

    database_url: str = "sqlite+aiosqlite:///./aliaz.db"
    app_name: str = "aliaz"
    app_version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Разрешённые хосты для TrustedHostMiddleware.
    # В продакшене задайте реальный домен через .env (ALLOWED_HOSTS=api.example.com).
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "testserver"]

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    jwt_refresh_expire_minutes: int = 60 * 24 * 7  # 7 дней

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
