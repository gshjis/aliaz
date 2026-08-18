"""Тесты конфигурации проекта (пакет config)."""

from config import Settings


def test_settings_defaults() -> None:
    """Проверить значения по умолчанию."""
    s = Settings()
    assert s.app_name == "aliaz"
    assert s.app_version == "0.1.0"
    assert s.debug is False
    assert s.host == "0.0.0.0"
    assert s.port == 8000
    assert s.jwt_secret == "change-me-in-production"
    assert s.jwt_algorithm == "HS256"
    assert s.jwt_expire_minutes == 60


def test_settings_env_override(monkeypatch) -> None:
    """Переменные окружения должны переопределять значения по умолчанию."""
    monkeypatch.setenv("APP_NAME", "testapp")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "30")

    s = Settings()
    assert s.app_name == "testapp"
    assert s.port == 9000
    assert s.debug is True
    assert s.jwt_expire_minutes == 30


def test_settings_case_insensitive(monkeypatch) -> None:
    """Имена переменных окружения нечувствительны к регистру."""
    monkeypatch.setenv("app_name", "lowercase")
    s = Settings()
    assert s.app_name == "lowercase"
