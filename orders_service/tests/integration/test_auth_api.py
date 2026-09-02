"""Pruebas de integración: autenticación JWT contra la API real (in-process)."""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestAuth:
    async def test_login_with_valid_credentials_returns_token(self, client: AsyncClient) -> None:
        response = await client.post(
            "/auth/token", data={"username": "demo", "password": "demo1234"}
        )
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    async def test_login_with_invalid_credentials_returns_401(self, client: AsyncClient) -> None:
        response = await client.post(
            "/auth/token", data={"username": "demo", "password": "wrong-password"}
        )
        assert response.status_code == 401

    async def test_orders_endpoint_requires_auth(self, client: AsyncClient) -> None:
        response = await client.get("/orders")
        assert response.status_code == 401

    async def test_orders_endpoint_rejects_invalid_token(self, client: AsyncClient) -> None:
        response = await client.get(
            "/orders", headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
