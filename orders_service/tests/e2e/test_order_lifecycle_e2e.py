"""Prueba E2E: simula el journey completo de un cliente real contra la API,
de principio a fin, tal como lo haría un consumidor externo del servicio:
login -> crear orden -> agregar items -> confirmar -> consultar -> cancelar
otra orden distinta. No usa mocks en ninguna capa.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestOrderLifecycleE2E:
    async def test_full_happy_path_lifecycle(self, client: AsyncClient) -> None:
        # 1. Login
        login_resp = await client.post(
            "/auth/token", data={"username": "demo", "password": "demo1234"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Crear orden
        create_resp = await client.post(
            "/orders", json={"customer_id": "cust-e2e", "currency": "MXN"}, headers=headers
        )
        assert create_resp.status_code == 201
        order_id = create_resp.json()["id"]

        # 3. Agregar dos items
        await client.post(
            f"/orders/{order_id}/items",
            json={
                "product_id": "prod-teclado",
                "product_name": "Teclado mecánico",
                "quantity": 1,
                "unit_price": "1299.00",
            },
            headers=headers,
        )
        item2_resp = await client.post(
            f"/orders/{order_id}/items",
            json={
                "product_id": "prod-mouse",
                "product_name": "Mouse inalámbrico",
                "quantity": 2,
                "unit_price": "349.50",
            },
            headers=headers,
        )
        assert item2_resp.status_code == 200
        assert item2_resp.json()["total_amount"] == "1998.00"

        # 4. Confirmar la orden
        confirm_resp = await client.post(f"/orders/{order_id}/confirm", headers=headers)
        assert confirm_resp.status_code == 200
        assert confirm_resp.json()["status"] == "confirmed"

        # 5. Consultar el detalle final y verificar consistencia
        get_resp = await client.get(f"/orders/{order_id}", headers=headers)
        assert get_resp.status_code == 200
        final_order = get_resp.json()
        assert final_order["status"] == "confirmed"
        assert len(final_order["items"]) == 2
        assert final_order["total_amount"] == "1998.00"

        # 6. No se puede agregar más items a una orden ya confirmada
        blocked_resp = await client.post(
            f"/orders/{order_id}/items",
            json={
                "product_id": "prod-extra",
                "product_name": "Extra",
                "quantity": 1,
                "unit_price": "10.00",
            },
            headers=headers,
        )
        assert blocked_resp.status_code == 409

        # 7. Ni se puede cancelar y luego confirmar
        cancel_resp = await client.post(f"/orders/{order_id}/cancel", json={}, headers=headers)
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "cancelled"

        reconfirm_resp = await client.post(f"/orders/{order_id}/confirm", headers=headers)
        assert reconfirm_resp.status_code == 409

    async def test_unauthenticated_user_cannot_access_orders(self, client: AsyncClient) -> None:
        response = await client.post("/orders", json={"customer_id": "cust-1"})
        assert response.status_code == 401
