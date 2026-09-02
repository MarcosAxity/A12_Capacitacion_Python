"""Adaptador in-memory de OrderRepository.

Útil para tests unitarios rápidos y como referencia de la forma mínima
que debe cumplir cualquier adaptador de persistencia (ver tests/contract).
"""
from __future__ import annotations

import copy

from orders.domain.entities import Order


class InMemoryOrderRepository:
    """Implementa el Protocol OrderRepository sin heredar de nada (duck typing)."""

    def __init__(self) -> None:
        self._storage: dict[str, Order] = {}

    async def save(self, order: Order) -> None:
        # Se guarda una copia profunda para simular la frontera de persistencia
        # real (evita que mutaciones posteriores en memoria "filtren" al storage).
        self._storage[order.id] = copy.deepcopy(order)

    async def get(self, order_id: str) -> Order | None:
        order = self._storage.get(order_id)
        return copy.deepcopy(order) if order is not None else None

    async def list(
        self, customer_id: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[Order]:
        orders = list(self._storage.values())
        if customer_id is not None:
            orders = [o for o in orders if o.customer_id == customer_id]
        orders.sort(key=lambda o: o.created_at)
        return [copy.deepcopy(o) for o in orders[offset : offset + limit]]

    async def delete(self, order_id: str) -> bool:
        return self._storage.pop(order_id, None) is not None
