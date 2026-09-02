"""Adaptador de infraestructura: implementa OrderRepository en memoria.

Podría reemplazarse por una versión con SQLAlchemy, Mongo, un ORM, etc.
sin tocar una sola línea de dominio o de aplicación: eso es justamente lo
que garantiza la regla de dependencia de Clean Architecture.
"""
from __future__ import annotations
from typing import Dict, List, Optional
from orders.application.ports.repositories import OrderRepository
from orders.domain.entities import Order


class InMemoryOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self._storage: Dict[str, Order] = {}

    def add(self, order: Order) -> None:
        self._storage[order.id] = order

    def get(self, order_id: str) -> Optional[Order]:
        return self._storage.get(order_id)

    def list(self) -> List[Order]:
        return list(self._storage.values())
