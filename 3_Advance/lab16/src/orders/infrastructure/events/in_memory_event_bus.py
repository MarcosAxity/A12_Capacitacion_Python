"""Adaptador de infraestructura: bus de eventos síncrono en memoria.

En un sistema real podría sustituirse por Kafka, RabbitMQ, SNS/SQS, etc.,
sin que la aplicación (casos de uso) se entere: solo depende de EventBus.
"""
from __future__ import annotations
from collections import defaultdict
from typing import Callable, Dict, List, Type
from orders.application.ports.event_bus import EventBus
from orders.domain.events import DomainEvent


class InMemoryEventBus(EventBus):
    def __init__(self) -> None:
        self._handlers: Dict[Type[DomainEvent], List[Callable]] = defaultdict(list)

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers[type(event)]:
            handler(event)
