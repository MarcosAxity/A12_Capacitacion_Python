"""Tests de integración de src/main.py usando httpx.AsyncClient contra la
app ASGI en memoria (sin levantar un servidor real)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from src.config import Settings, get_settings
from src.main import app

TEST_ENV = {
    "secret_key": "una-clave-de-pruebas-larga-y-segura",
    "database_url": "postgresql://user:pass@localhost:5432/testdb",
}


@pytest.fixture(autouse=True)
def override_settings(monkeypatch: pytest.MonkeyPatch):
    """Inyecta settings de prueba y limpia el cache antes/después de cada test."""
    monkeypatch.setenv("APP_SECRET_KEY", TEST_ENV["secret_key"])
    monkeypatch.setenv("APP_DATABASE_URL", TEST_ENV["database_url"])
    monkeypatch.setenv("APP_ENVIRONMENT", "development")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_health_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_config_endpoint_masks_secrets() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/config")

    assert resp.status_code == 200
    body = resp.json()
    assert body["secret_key"] == "**********"
    assert body["database_url"] == "**********"
    assert TEST_ENV["secret_key"] not in str(body)


@pytest.mark.anyio
async def test_whoami_endpoint_never_leaks_raw_secret() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/whoami")

    assert resp.status_code == 200
    body = resp.json()
    assert "secret_fingerprint" in body
    assert TEST_ENV["secret_key"] not in str(body)
    assert len(body["secret_fingerprint"]) == 12
