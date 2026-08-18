"""Интеграционные тесты роутера аутентификации (api.api.auth)."""

from httpx import AsyncClient


async def _register(
    client: AsyncClient, nickname: str, email: str
) -> dict[str, object]:
    """Зарегистрировать пользователя и вернуть тело ответа."""
    resp = await client.post(
        "/auth/register",
        json={
            "nickname": nickname,
            "email": email,
            "password": "password123",
        },
    )
    assert resp.status_code == 201
    return resp.json()


async def test_register_success(client: AsyncClient) -> None:
    """Регистрация возвращает JWT-токен."""
    body = await _register(client, "alice", "alice@example.com")
    assert "access_token" in body
    assert body["token_type"] == "bearer"


async def test_register_duplicate(client: AsyncClient) -> None:
    """Повторная регистрация с теми же данными — 409."""
    await _register(client, "bob", "bob@example.com")
    resp = await client.post(
        "/auth/register",
        json={
            "nickname": "bob",
            "email": "bob@example.com",
            "password": "password123",
        },
    )
    assert resp.status_code == 409


async def test_login_success(client: AsyncClient) -> None:
    """Вход с валидными данными возвращает токен."""
    await _register(client, "carol", "carol@example.com")
    resp = await client.post(
        "/auth/login",
        json={"email": "carol@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_invalid_password(client: AsyncClient) -> None:
    """Вход с неверным паролем — 401."""
    await _register(client, "dave", "dave@example.com")
    resp = await client.post(
        "/auth/login",
        json={"email": "dave@example.com", "password": "wrongpass"},
    )
    assert resp.status_code == 401


async def test_login_unknown_email(client: AsyncClient) -> None:
    """Вход с неизвестным email — 401."""
    resp = await client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert resp.status_code == 401


async def test_me_unauthorized(client: AsyncClient) -> None:
    """Доступ к /auth/me без токена — 401."""
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_me_invalid_token(client: AsyncClient) -> None:
    """Доступ к /auth/me с невалидным токеном — 401."""
    resp = await client.get(
        "/auth/me", headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert resp.status_code == 401


async def test_me_authorized(client: AsyncClient) -> None:
    """Доступ к /auth/me с валидным токеном возвращает данные пользователя."""
    body = await _register(client, "eve", "eve@example.com")
    token = body["access_token"]
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["nickname"] == "eve"
    assert data["email"] == "eve@example.com"
    assert "id" in data
