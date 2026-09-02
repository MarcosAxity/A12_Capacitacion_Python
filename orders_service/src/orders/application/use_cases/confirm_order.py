from __future__ import annotations

from dataclasses import dataclass

from orders.application.dto import OrderDTO
from orders.application.mappers import order_to_dto
from orders.domain.exceptions import OrderNotFoundError
from orders.domain.ports.event_publisher import EventPublisher
from orders.domain.ports.repository import OrderRepository


@dataclass(slots=True)
class ConfirmOrderUseCase:
    repository: OrderRepository
    event_publisher: EventPublisher

    async def execute(self, order_id: str) -> OrderDTO:
        order = await self.repository.get(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)

        order.confirm()

        await self.repository.save(order)
        await self.event_publisher.publish(order.pull_events())
        return order_to_dto(order)
