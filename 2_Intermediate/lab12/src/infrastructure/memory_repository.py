"""Adaptador de persistencia en memoria.

Implementa el puerto `OrderRepository` (duck typing vía Protocol: no
hereda de nada, simplemente expone los mismos métodos). Útil para
tests rápidos y prototipado.
"""

from typing import Dict, List, Optional

from src.domain.models import Order


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._orders: Dict[str, Order] = {}

    def add(self, order: Order) -> None:
        self._orders[order.id] = order

    def get(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    def list_all(self) -> List[Order]:
        return list(self._orders.values())

    def update(self, order: Order) -> None:
        if order.id not in self._orders:
            raise KeyError(f"No se puede actualizar un pedido inexistente: {order.id}")
        self._orders[order.id] = order
