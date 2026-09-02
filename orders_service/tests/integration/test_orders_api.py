"""Pruebas de integración de los endpoints de Orders: validan la API
completa (routing, validación Pydantic, casos de uso, persistencia real
en SQLite vía SQLAlchemy) sin mockear nada, pero sin requerir Docker.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestOrdersApi:
    async def test_create_order(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        response = await client.post(
            "/orders", json={"customer_id": "cust-1", "currency": "MXN"}, headers=auth_headers
        )
        assert response.status_code == 201
        body = response.json()
        assert body["customer_id"] == "cust-1"
        assert body["status"] == "created"
        assert body["items"] == []

    async def test_create_order_validates_payload(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post("/orders", json={"customer_id": ""}, headers=auth_headers)
        assert response.status_code == 422

    async def test_get_order_not_found_returns_404(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get("/orders/does-not-exist", headers=auth_headers)
        assert response.status_code == 404
        body = response.json()
        assert body["error_type"] == "OrderNotFoundError"

    async def test_add_item_and_get_order(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        create_resp = await client.post(
            "/orders", json={"customer_id": "cust-1"}, headers=auth_headers
        )
        order_id = create_resp.json()["id"]

        add_resp = await client.post(
            f"/orders/{order_id}/items",
            json={
                "product_id": "prod-1",
                "product_name": "Teclado mecánico",
                "quantity": 2,
                "unit_price": "499.99",
            },
            headers=auth_headers,
        )

        assert add_resp.status_code == 200
        body = add_resp.json()
        assert len(body["items"]) == 1
        assert body["total_amount"] == "999.98"

    async def test_add_item_with_invalid_quantity_returns_422(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        create_resp = await client.post(
            "/orders", json={"customer_id": "cust-1"}, headers=auth_headers
        )
        order_id = create_resp.json()["id"]

        response = await client.post(
            f"/orders/{order_id}/items",
            json={
                "product_id": "prod-1",
                "product_name": "Teclado",
                "quantity": 0,
                "unit_price": "10.00",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_confirm_order_flow(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        create_resp = await client.post(
            "/orders", json={"customer_id": "cust-1"}, headers=auth_headers
        )
        order_id = create_resp.json()["id"]
        await client.post(
            f"/orders/{order_id}/items",
            json={
                "product_id": "prod-1",
                "product_name": "Mouse",
                "quantity": 1,
                "unit_price": "199.00",
            },
            headers=auth_headers,
        )

        confirm_resp = await client.post(f"/orders/{order_id}/confirm", headers=auth_headers)

        assert confirm_resp.status_code == 200
        assert confirm_resp.json()["status"] == "confirmed"

    async def test_confirm_empty_order_returns_422(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        create_resp = await client.post(
            "/orders", json={"customer_id": "cust-1"}, headers=auth_headers
        )
        order_id = create_resp.json()["id"]

        response = await client.post(f"/orders/{order_id}/confirm", headers=auth_headers)
        assert response.status_code == 422

    async def test_cancel_order(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        create_resp = await client.post(
            "/orders", json={"customer_id": "cust-1"}, headers=auth_headers
        )
        order_id = create_resp.json()["id"]

        response = await client.post(
            f"/orders/{order_id}/cancel", json={"reason": "cliente canceló"}, headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    async def test_cancel_twice_returns_409(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        create_resp = await client.post(
            "/orders", json={"customer_id": "cust-1"}, headers=auth_headers
        )
        order_id = create_resp.json()["id"]
        await client.post(f"/orders/{order_id}/cancel", json={}, headers=auth_headers)

        response = await client.post(f"/orders/{order_id}/cancel", json={}, headers=auth_headers)

        assert response.status_code == 409
        assert response.json()["error_type"] == "InvalidOrderStateError"

    async def test_list_orders_filtered_by_customer(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        await client.post("/orders", json={"customer_id": "cust-list-1"}, headers=auth_headers)
        await client.post("/orders", json={"customer_id": "cust-list-1"}, headers=auth_headers)
        await client.post("/orders", json={"customer_id": "cust-list-2"}, headers=auth_headers)

        response = await client.get(
            "/orders", params={"customer_id": "cust-list-1"}, headers=auth_headers
        )

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
        assert all(o["customer_id"] == "cust-list-1" for o in body)


@pytest.mark.integration
class TestObservabilityEndpoints:
    async def test_health_endpoint(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    async def test_metrics_endpoint_exposes_prometheus_format(
        self, client: AsyncClient
    ) -> None:
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    async def test_response_includes_request_id_header(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert "X-Request-ID" in response.headers
