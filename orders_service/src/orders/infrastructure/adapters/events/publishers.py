"""Adaptadores del puerto EventPublisher."""
from __future__ import annotations

import logging

from orders.domain.events import DomainEvent

logger = logging.getLogger("orders.events")


class LoggingEventPublisher:
    """Adaptador de producción simplificado: registra los eventos en el log
    estructurado. En un sistema real se sustituiría por un adaptador de
    Kafka/RabbitMQ/SNS sin tocar la capa de aplicación (ver InMemory abajo
    para la variante usada en tests).
    """

    async def publish(self, events: list[DomainEvent]) -> None:
        for event in events:
            logger.info(
                "domain_event_published",
                extra={"event_type": type(event).__name__, "payload": str(event)},
            )


class InMemoryEventPublisher:
    """Adaptador de pruebas: acumula los eventos publicados para poder
    hacer aserciones sobre ellos en los tests.
    """

    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    async def publish(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)
