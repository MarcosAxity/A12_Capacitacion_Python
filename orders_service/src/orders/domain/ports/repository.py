"""Puerto de persistencia (patrón Repository) usando typing.Protocol.

Cualquier adaptador (in-memory, SQLAlchemy, etc.) que implemente esta forma
es válido para la capa de aplicación, sin necesidad de heredar de una clase
base — cumple DIP (Dependency Inversion Principle) de forma "pythónica".
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from orders.domain.entities import Order


@runtime_checkable
class OrderRepository(Protocol):
    async def save(self, order: Order) -> None:
        """Inserta o actualiza (upsert) una orden completa."""
        ...

    async def get(self, order_id: str) -> Order | None:
        """Retorna la orden o None si no existe."""
        ...

    async def list(
        self, customer_id: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[Order]:
        """Lista órdenes, opcionalmente filtradas por cliente, paginadas."""
        ...

    async def delete(self, order_id: str) -> bool:
        """Elimina una orden. Retorna True si existía."""
        ...
