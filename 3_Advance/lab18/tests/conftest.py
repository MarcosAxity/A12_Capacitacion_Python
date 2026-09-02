import socket
import threading
import time

import pytest
import uvicorn

from orders_api.main import app as api_app, _reset_db
from orders_cli.config import Settings
from orders_cli import client as client_module


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_api_url():
    """Levanta la API FastAPI real en un thread en background para que los
    tests del CLI ejerciten el flujo HTTP completo (Typer -> httpx -> API)."""
    port = _free_port()
    config = uvicorn.Config(api_app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(50):
        if server.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture(autouse=True)
def reset_db():
    _reset_db()
    yield
    _reset_db()


@pytest.fixture
def patch_orders_client(monkeypatch, live_api_url):
    """Reemplaza OrdersClient para que apunte al servidor real de pruebas
    levantado por `live_api_url`, en vez de depender de variables de
    entorno externas."""

    def _factory(settings=None, transport=None):
        return client_module.OrdersClient(
            settings=settings or Settings(api_base_url=live_api_url),
            transport=transport,
        )

    monkeypatch.setattr("orders_cli.cli.OrdersClient", _factory)
    return _factory
