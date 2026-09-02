"""Puerto de publicación de eventos de dominio."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from orders.domain.events import DomainEvent


@runtime_checkable
class EventPublisher(Protocol):
    async def publish(self, events: list[DomainEvent]) -> None:
        """Publica una lista de eventos de dominio (a un log, broker, etc.)."""
        ...
