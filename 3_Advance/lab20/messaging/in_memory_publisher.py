"""Adaptador en memoria: captura los eventos publicados sin broker externo.

Útil para pruebas unitarias (aisladas, rápidas, deterministas) y para
demos locales donde no hay un RabbitMQ/Redis corriendo.
"""
from __future__ import annotations

from generated import orders_pb2


class InMemoryPublisher:
    """Implementación de EventPublisher que guarda los eventos en una lista."""

    def __init__(self) -> None:
        self.published_events: list[orders_pb2.OrderCreatedEvent] = []

    def publish_order_created(self, event: orders_pb2.OrderCreatedEvent) -> None:
        self.published_events.append(event)

    def close(self) -> None:
        pass
