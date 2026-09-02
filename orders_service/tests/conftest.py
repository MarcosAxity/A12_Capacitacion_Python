"""Fixtures compartidas para integración y E2E: construyen una app FastAPI
completa contra una base de datos SQLite en archivo temporal (aislada por
test) y exponen un AsyncClient de httpx listo para llamar a la API.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from orders.infrastructure.adapters.db.models import Base
from orders.infrastructure.api.main import create_app
from orders.infrastructure.config import Settings


@pytest_asyncio.fixture
async def test_settings(tmp_path) -> Settings:
    db_file = tmp_path / "test_orders.db"
    return Settings(
        database_url=f"sqlite+aiosqlite:///{db_file}",
        jwt_secret_key="test-secret-key-with-at-least-32-bytes-long",
        environment="test",
        sql_echo=False,
    )


@pytest_asyncio.fixture
async def app(test_settings: Settings):
    fastapi_app = create_app(settings=test_settings)
    async with fastapi_app.router.lifespan_context(fastapi_app):
        container = fastapi_app.state.container
        async with container.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield fastapi_app


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    response = await client.post(
        "/auth/token", data={"username": "demo", "password": "demo1234"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
