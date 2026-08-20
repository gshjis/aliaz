"""Интеграционные тесты роутера слов (api.api.words)."""

from httpx import AsyncClient


async def _register_and_token(client: AsyncClient, nickname: str, email: str) -> str:
    """Зарегистрировать пользователя и вернуть JWT-токен."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={"nickname": nickname, "email": email, "password": "password123"},
    )
    assert resp.status_code == 201
    return str(resp.json()["access_token"])


async def test_create_word(client: AsyncClient) -> None:
    """Создание слова возвращает перевод от заглушки."""
    token = await _register_and_token(client, "usr1", "usr1@example.com")
    resp = await client.post(
        "/api/v1/words",
        json={"word_en": "hello"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["word_en"] == "hello"
    assert body["translation"] is not None
    assert (
        "hello" in body["translation"].lower()
        or "привет" in body["translation"].lower()
    )
    assert body["id"] is not None
    assert "transcription" in body
    assert "corrected_word" in body


async def test_create_word_unauthorized(client: AsyncClient) -> None:
    """Создание слова без токена — 401."""
    resp = await client.post("/api/v1/words", json={"word_en": "hello"})
    assert resp.status_code == 401


async def test_list_words(client: AsyncClient) -> None:
    """Список слов возвращает только слова текущего пользователя."""
    token = await _register_and_token(client, "usr2", "usr2@example.com")
    await client.post(
        "/api/v1/words",
        json={"word_en": "one"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/api/v1/words",
        json={"word_en": "two"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        "/api/v1/words", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    words = resp.json()
    assert len(words) == 2
    assert {w["word_en"] for w in words} == {"one", "two"}


async def test_get_word(client: AsyncClient) -> None:
    """Получение одного слова по id."""
    token = await _register_and_token(client, "usr3", "usr3@example.com")
    created = await client.post(
        "/api/v1/words",
        json={"word_en": "cat"},
        headers={"Authorization": f"Bearer {token}"},
    )
    word_id = created.json()["id"]
    resp = await client.get(
        f"/api/v1/words/{word_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["word_en"] == "cat"


async def test_get_word_not_found(client: AsyncClient) -> None:
    """Получение несуществующего слова — 404."""
    token = await _register_and_token(client, "usr4", "usr4@example.com")
    resp = await client.get(
        "/api/v1/words/999", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404


async def test_delete_word(client: AsyncClient) -> None:
    """Удаление слова возвращает 204 и затем слово недоступно."""
    token = await _register_and_token(client, "usr5", "usr5@example.com")
    created = await client.post(
        "/api/v1/words",
        json={"word_en": "dog"},
        headers={"Authorization": f"Bearer {token}"},
    )
    word_id = created.json()["id"]
    resp = await client.delete(
        f"/api/v1/words/{word_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 204
    resp2 = await client.get(
        f"/api/v1/words/{word_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp2.status_code == 404


async def test_word_isolation_between_users(client: AsyncClient) -> None:
    """Пользователь не видит чужие слова (404 при доступе к чужому слову)."""
    token_a = await _register_and_token(client, "owner", "owner@example.com")
    token_b = await _register_and_token(client, "other", "other@example.com")
    created = await client.post(
        "/api/v1/words",
        json={"word_en": "secret"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    word_id = created.json()["id"]
    resp = await client.get(
        f"/api/v1/words/{word_id}", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert resp.status_code == 404
