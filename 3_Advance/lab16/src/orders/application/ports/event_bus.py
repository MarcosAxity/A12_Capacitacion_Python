"""Puerto del bus de eventos de dominio."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable, Type
from orders.domain.events import DomainEvent


class EventBus(ABC):
    @abstractmethod
    def subscribe(self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        ...

    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        ...
