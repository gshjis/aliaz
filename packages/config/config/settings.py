"""Глобальная конфигурация проекта."""

import json
from pydantic import field_validator
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
    # В продакшене задайте реальный домен через .env (ALLOWED_HOSTS=["api.example.com"]).
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "testserver"]

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v: str | list[str]) -> list[str]:
        """Парсить ALLOWED_HOSTS из JSON-строки или вернуть как есть."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Если не JSON, считаем это одним хостом
                return [v.strip()]
        return v

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    jwt_refresh_expire_minutes: int = 60 * 24 * 7  # 7 дней

    # OpenAI
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://openrouter.ai/api/v1"

    # CORS
    allowed_origins: list[str] | None = None

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: str | list[str] | None) -> list[str] | None:
        """Парсить ALLOWED_ORIGINS из JSON-строки или вернуть как есть."""
        if v is None:
            return None
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Если не JSON, считаем это одним origins
                return [v.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
