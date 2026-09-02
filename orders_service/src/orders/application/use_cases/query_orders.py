"""Casos de uso de solo lectura (queries). Se separan de los comandos
siguiendo el espíritu de CQRS, aunque comparten el mismo puerto de
repositorio por simplicidad en este proyecto.
"""
from __future__ import annotations

from dataclasses import dataclass

from orders.application.dto import OrderDTO
from orders.application.mappers import order_to_dto
from orders.domain.exceptions import OrderNotFoundError
from orders.domain.ports.repository import OrderRepository


@dataclass(slots=True)
class GetOrderUseCase:
    repository: OrderRepository

    async def execute(self, order_id: str) -> OrderDTO:
        order = await self.repository.get(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        return order_to_dto(order)


@dataclass(slots=True)
class ListOrdersUseCase:
    repository: OrderRepository

    async def execute(
        self, customer_id: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[OrderDTO]:
        orders = await self.repository.list(customer_id=customer_id, limit=limit, offset=offset)
        return [order_to_dto(o) for o in orders]
