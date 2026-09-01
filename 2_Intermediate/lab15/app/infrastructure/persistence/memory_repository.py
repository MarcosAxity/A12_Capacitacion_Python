"""
ADAPTADOR de infraestructura: repositorio en memoria.

Implementa `OrderRepositoryPort` usando un diccionario en RAM. Es ideal
para pruebas rápidas de dominio/aplicación y para desarrollo local, sin
necesidad de levantar una base de datos.

Nótese que esta clase NO hereda de ninguna clase abstracta explícita:
gracias a `typing.Protocol`, basta con implementar los mismos métodos
(save, get_by_id, list_all) para que el type-checker (y el propio
Python en runtime, vía `runtime_checkable`) la reconozca como una
implementación válida de OrderRepositoryPort.
"""

from __future__ import annotations

from app.domain.entities import Order


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._storage: dict[str, Order] = {}

    def save(self, order: Order) -> None:
        self._storage[order.id] = order

    def get_by_id(self, order_id: str) -> Order | None:
        return self._storage.get(order_id)

    def list_all(self) -> list[Order]:
        return list(self._storage.values())
