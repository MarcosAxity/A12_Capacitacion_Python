"""Adaptador de infraestructura: Unit of Work en memoria.

Responsabilidades:
1. Exponer el repositorio dentro de una misma transacción lógica.
2. Al hacer commit(): "persistir" los cambios (aquí ya están en memoria)
   y luego recolectar los eventos de dominio acumulados en las entidades
   tocadas durante la transacción, publicándolos recién en ese momento.
3. Si no se llama a commit() (por ejemplo porque hubo una excepción), no
   se publica ningún evento: el rollback es implícito.
"""
from __future__ import annotations
from orders.application.ports.event_bus import EventBus
from orders.application.ports.unit_of_work import UnitOfWork
from orders.infrastructure.persistence.in_memory_repository import InMemoryOrderRepository


class InMemoryUnitOfWork(UnitOfWork):
    def __init__(self, repository: InMemoryOrderRepository, event_bus: EventBus):
        self.orders = repository
        self._event_bus = event_bus

    def commit(self) -> None:
        pending_events = []
        for order in self.orders.list():
            pending_events.extend(order.pull_domain_events())

        for event in pending_events:
            self._event_bus.publish(event)

    def rollback(self) -> None:
        # En este adaptador en memoria no hay nada físico que revertir; en
        # un UoW real con SQLAlchemy aquí iría `self._session.rollback()`.
        pass
