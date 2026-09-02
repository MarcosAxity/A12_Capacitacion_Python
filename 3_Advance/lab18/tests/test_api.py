from fastapi.testclient import TestClient

from orders_api.main import app, _reset_db


def setup_function() -> None:
    _reset_db()


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_list_order() -> None:
    client = TestClient(app)
    payload = {"customer": "Marcos", "items": ["laptop", "mouse"], "total": 1500.0}
    create_response = client.post("/orders", json=payload)
    assert create_response.status_code == 201
    order = create_response.json()
    assert order["customer"] == "Marcos"
    assert order["status"] == "pending"

    list_response = client.get("/orders")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_delete_order() -> None:
    client = TestClient(app)
    payload = {"customer": "Ana", "items": ["teclado"], "total": 500.0}
    order = client.post("/orders", json=payload).json()

    delete_response = client.delete(f"/orders/{order['id']}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/orders/{order['id']}")
    assert get_response.status_code == 404


def test_delete_nonexistent_order_returns_404() -> None:
    client = TestClient(app)
    response = client.delete("/orders/no-existe")
    assert response.status_code == 404
