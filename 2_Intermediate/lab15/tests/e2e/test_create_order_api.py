"""
PRUEBAS END-TO-END (E2E).

Levantan la aplicación FastAPI completa (con TestClient) y golpean los
endpoints HTTP tal como lo haría un cliente real. Verifican todo el
flujo: request HTTP -> schema Pydantic -> DTO -> caso de uso -> entidad
de dominio -> puerto de repositorio -> puerto de notificación -> DTO de
salida -> response HTTP.

Para mantener las pruebas rápidas y aisladas, sobreescribimos las
dependencias de FastAPI para usar un `Container` en memoria "fresco"
en cada test, en vez del contenedor global de la app (que podría usar
SQLite en disco).
"""

import pytest
from app.api.main import app, get_create_order_use_case, get_get_order_use_case
from app.container import Container
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    test_container = Container(use_sqlalchemy=False)

    app.dependency_overrides[get_create_order_use_case] = (
        lambda: test_container.create_order_use_case
    )
    app.dependency_overrides[get_get_order_use_case] = (
        lambda: test_container.get_order_use_case
    )

    with TestClient(app) as test_client:
        test_client.notifier = (
            test_container.notifier
        )  # para inspeccionar notificaciones enviadas
        yield test_client

    app.dependency_overrides.clear()


def test_create_order_returns_201_with_total_and_status(client):
    payload = {
        "customer_id": "cust-42",
        "items": [
            {"product_id": "SKU-1", "quantity": 2, "unit_price": "10.00"},
            {"product_id": "SKU-2", "quantity": 1, "unit_price": "5.00"},
        ],
    }

    response = client.post("/orders", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["customer_id"] == "cust-42"
    assert body["status"] == "CREATED"
    assert body["total"] == "25.00"
    assert len(body["items"]) == 2


def test_create_order_triggers_notification_adapter(client):
    payload = {
        "customer_id": "cust-42",
        "items": [{"product_id": "SKU-1", "quantity": 1, "unit_price": "10.00"}],
    }

    response = client.post("/orders", json=payload)
    order_id = response.json()["id"]

    assert len(client.notifier.sent_notifications) == 1
    notification = client.notifier.sent_notifications[0]
    assert notification.payload["order_id"] == order_id
    assert notification.payload["event"] == "order_created"


def test_create_order_with_empty_items_returns_422(client):
    payload = {"customer_id": "cust-42", "items": []}

    response = client.post("/orders", json=payload)

    assert response.status_code == 422


def test_get_order_after_create_returns_same_order(client):
    create_payload = {
        "customer_id": "cust-7",
        "items": [{"product_id": "SKU-9", "quantity": 3, "unit_price": "2.50"}],
    }
    created = client.post("/orders", json=create_payload).json()

    response = client.get(f"/orders/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["total"] == "7.50"


def test_get_unknown_order_returns_404(client):
    response = client.get("/orders/no-existe")

    assert response.status_code == 404
