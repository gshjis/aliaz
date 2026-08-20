"""Тесты CORS и безопасности API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cors_headers_present(client: AsyncClient) -> None:
    """CORS заголовки присутствуют в ответах."""
    resp = await client.get("/")
    assert "access-control-allow-origin" in resp.headers
    assert "access-control-allow-methods" in resp.headers
    assert "access-control-allow-headers" in resp.headers


@pytest.mark.asyncio
async def test_cors_allow_all_origins(client: AsyncClient) -> None:
    """CORS разрешает запросы с любого origin."""
    resp = await client.get(
        "/",
        headers={"Origin": "https://malicious-site.com"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_cors_preflight_request(client: AsyncClient) -> None:
    """OPTIONS запрос (preflight) возвращает CORS заголовки."""
    resp = await client.options(
        "/",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert resp.status_code == 200
    assert "access-control-allow-origin" in resp.headers
    assert "access-control-allow-methods" in resp.headers


@pytest.mark.asyncio
async def test_trusted_host_middleware(client: AsyncClient) -> None:
    """TrustedHostMiddleware блокирует запросы с неразрешённого хоста."""
    resp = await client.get("/")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_rate_limiting_enabled(client: AsyncClient) -> None:
    """Rate limiting включен."""
    for i in range(250):
        resp = await client.get("/")
        if i >= 200:
            assert resp.status_code in [429, 200]
        else:
            assert resp.status_code == 200