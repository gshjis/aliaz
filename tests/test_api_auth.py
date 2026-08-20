"""Интеграционные тесты роутера аутентификации (api.api.auth)."""

from httpx import AsyncClient

from database.connection import get_db


async def _register(
    client: AsyncClient, nickname: str, email: str
) -> dict[str, object]:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"nickname": nickname, "email": email, "password": "password123"},
    )
    assert resp.status_code == 201
    return dict(resp.json())


async def test_register_success(client: AsyncClient) -> None:
    """Регистрация возвращает access и refresh токены."""
    body = await _register(client, "alice", "alice@example.com")
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_register_duplicate(client: AsyncClient) -> None:
    """Повторная регистрация с теми же данными — 409."""
    await _register(client, "bob", "bob@example.com")
    resp = await client.post(
        "/api/v1/auth/register",
        json={"nickname": "bob", "email": "bob@example.com", "password": "password123"},
    )
    assert resp.status_code == 409


async def test_login_success(client: AsyncClient) -> None:
    """Вход с валидными данными возвращает токены."""
    await _register(client, "carol", "carol@example.com")
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "carol@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_login_invalid_password(client: AsyncClient) -> None:
    """Вход с неверным паролем — 401."""
    await _register(client, "dave", "dave@example.com")
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "dave@example.com", "password": "wrongpass"},
    )
    assert resp.status_code == 401


async def test_login_unknown_email(client: AsyncClient) -> None:
    """Вход с неизвестным email — 401."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert resp.status_code == 401


async def test_me_unauthorized(client: AsyncClient) -> None:
    """Доступ к /auth/me без токена — 401."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_invalid_token(client: AsyncClient) -> None:
    """Доступ к /auth/me с невалидным токеном — 401."""
    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert resp.status_code == 401


async def test_me_authorized(client: AsyncClient) -> None:
    """Доступ к /auth/me с валидным токеном возвращает данные пользователя."""
    body = await _register(client, "eve", "eve@example.com")
    token = body["access_token"]
    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["nickname"] == "eve"
    assert data["email"] == "eve@example.com"
    assert "id" in data


async def test_refresh_success(client: AsyncClient) -> None:
    """Обновление токена возвращает новую пару токенов."""
    body = await _register(client, "frank", "frank@example.com")
    refresh_token = body["refresh_token"]
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["access_token"] != body["access_token"]


async def test_refresh_invalid_token(client: AsyncClient) -> None:
    """Обновление с невалидным refresh-токеном — 401."""
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "not.a.valid.token"}
    )
    assert resp.status_code == 401


async def test_refresh_expired_token(client: AsyncClient) -> None:
    """Просроченный refresh-токен отклоняется — 401."""
    from datetime import datetime, timedelta, UTC
    import jwt
    from config.settings import settings

    # Регистрируем пользователя через API
    body = await _register(client, "expired_user", "expired@example.com")

    # Получаем user_id через /auth/me
    access_token = body["access_token"]
    resp_me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert resp_me.status_code == 200
    user_id = resp_me.json()["id"]

    # Создаем просроченный refresh-токен
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now - timedelta(hours=1),
        "exp": now - timedelta(minutes=1),
        "type": "refresh",
        "jti": "expired-jti",
    }

    expired_token = jwt.encode(
        payload, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )

    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": expired_token}
    )
    assert resp.status_code == 401


async def test_refresh_rejects_access_token(client: AsyncClient) -> None:
    """Access-токен нельзя использовать как refresh-токен — 401."""
    body = await _register(client, "grace", "grace@example.com")
    access_token = body["access_token"]
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": access_token}
    )
    assert resp.status_code == 401
