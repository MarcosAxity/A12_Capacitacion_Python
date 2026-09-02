from __future__ import annotations

from dataclasses import dataclass

from orders.application.dto import AddItemInput, OrderDTO
from orders.application.mappers import order_to_dto
from orders.domain.exceptions import OrderNotFoundError
from orders.domain.ports.event_publisher import EventPublisher
from orders.domain.ports.repository import OrderRepository
from orders.domain.value_objects import ProductRef


@dataclass(slots=True)
class AddItemToOrderUseCase:
    repository: OrderRepository
    event_publisher: EventPublisher

    async def execute(self, data: AddItemInput) -> OrderDTO:
        order = await self.repository.get(data.order_id)
        if order is None:
            raise OrderNotFoundError(data.order_id)

        product = ProductRef(product_id=data.product_id, name=data.product_name)
        order.add_item(product, data.quantity, data.unit_price)

        await self.repository.save(order)
        await self.event_publisher.publish(order.pull_events())
        return order_to_dto(order)
