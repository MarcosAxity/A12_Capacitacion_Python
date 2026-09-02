"""Repositorio en memoria (suficiente para efectos de este módulo,
que se centra en empaquetado/CI-CD y no en arquitectura)."""

from __future__ import annotations

from uuid import UUID

from orders_api.models import Order


class OrderNotFoundError(Exception):
    pass


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._orders: dict[UUID, Order] = {}

    def add(self, order: Order) -> Order:
        self._orders[order.id] = order
        return order

    def get(self, order_id: UUID) -> Order:
        try:
            return self._orders[order_id]
        except KeyError as exc:
            raise OrderNotFoundError(str(order_id)) from exc

    def list(self) -> list[Order]:
        return list(self._orders.values())

    def delete(self, order_id: UUID) -> None:
        try:
            del self._orders[order_id]
        except KeyError as exc:
            raise OrderNotFoundError(str(order_id)) from exc
