"""Cliente HTTP de la API de Orders, usado por el CLI.

Se aisla en su propia clase (en vez de llamar a httpx directamente desde
los comandos Typer) para poder inyectar un `transport` de prueba en los
tests, sin necesidad de levantar un servidor real.
"""
from __future__ import annotations

from typing import List, Optional

import httpx

from .config import Settings, get_settings


class OrdersClient:
    def __init__(self, settings: Optional[Settings] = None, transport: Optional[httpx.BaseTransport] = None):
        self.settings = settings or get_settings()
        headers = {}
        if self.settings.api_token:
            headers["Authorization"] = f"Bearer {self.settings.api_token}"
        self._client = httpx.Client(
            base_url=self.settings.api_base_url,
            timeout=self.settings.api_timeout,
            headers=headers,
            transport=transport,
        )

    def list_orders(self, status: Optional[str] = None) -> list:
        params = {"status": status} if status else None
        response = self._client.get("/orders", params=params)
        response.raise_for_status()
        return response.json()

    def create_order(self, customer: str, items: List[str], total: float) -> dict:
        payload = {"customer": customer, "items": items, "total": total}
        response = self._client.post("/orders", json=payload)
        response.raise_for_status()
        return response.json()

    def delete_order(self, order_id: str) -> bool:
        response = self._client.delete(f"/orders/{order_id}")
        response.raise_for_status()
        return response.status_code == 204

    def close(self) -> None:
        try:
            self._client.close()
        except AttributeError:
            # Algunos transports de prueba (p. ej. httpx.ASGITransport en
            # ciertas versiones) no implementan close(); es seguro ignorarlo.
            pass

    def __enter__(self) -> "OrdersClient":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
