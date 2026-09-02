from __future__ import annotations

from fastapi.testclient import TestClient

from orders_api.main import create_app

client = TestClient(create_app())


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.1.0"


def test_create_and_get_order() -> None:
    payload = {"customer": "Marcos", "item": "Teclado", "quantity": 2, "unit_price": 45.5}
    created = client.post("/orders", json=payload)
    assert created.status_code == 201
    order = created.json()
    assert order["customer"] == "Marcos"
    assert order["status"] == "pending"

    fetched = client.get(f"/orders/{order['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == order["id"]


def test_list_orders_includes_created() -> None:
    client.post(
        "/orders",
        json={"customer": "Ana", "item": "Mouse", "quantity": 1, "unit_price": 20.0},
    )
    resp = client.get("/orders")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_get_order_not_found() -> None:
    resp = client.get("/orders/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_delete_order() -> None:
    created = client.post(
        "/orders",
        json={"customer": "Luis", "item": "Monitor", "quantity": 1, "unit_price": 199.99},
    )
    order_id = created.json()["id"]
    deleted = client.delete(f"/orders/{order_id}")
    assert deleted.status_code == 204

    missing = client.get(f"/orders/{order_id}")
    assert missing.status_code == 404


def test_create_order_validation_error() -> None:
    resp = client.post(
        "/orders",
        json={"customer": "", "item": "X", "quantity": 0, "unit_price": -1},
    )
    assert resp.status_code == 422
