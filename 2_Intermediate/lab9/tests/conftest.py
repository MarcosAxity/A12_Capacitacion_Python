import socket
import threading
import time

import pytest
import uvicorn
from app.main import app


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def server_url():
    """Levanta la app FastAPI real (uvicorn) en un hilo, para que los tests
    la golpeen con peticiones HTTP reales usando aiohttp."""
    port = _find_free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    while not server.started:
        time.sleep(0.05)

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=5)
