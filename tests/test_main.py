"""Тесты для API приложения."""

from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_root() -> None:
    """Тест корневого эндпоинта."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Welcome to aliaz API"}
