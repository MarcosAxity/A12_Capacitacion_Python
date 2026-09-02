"""Caso de uso: crear una orden nueva.

Un caso de uso orquesta el dominio y los puertos, pero NO contiene reglas
de negocio propias (esas viven en `Order`). Depende únicamente de
Protocols (puertos), nunca de implementaciones concretas -> DIP.
"""
from __future__ import annotations

from dataclasses import dataclass

from orders.application.dto import CreateOrderInput, OrderDTO
from orders.application.mappers import order_to_dto
from orders.domain.entities import Order
from orders.domain.ports.event_publisher import EventPublisher
from orders.domain.ports.repository import OrderRepository


@dataclass(slots=True)
class CreateOrderUseCase:
    repository: OrderRepository
    event_publisher: EventPublisher

    async def execute(self, data: CreateOrderInput) -> OrderDTO:
        order = Order.create(customer_id=data.customer_id, currency=data.currency)
        await self.repository.save(order)
        await self.event_publisher.publish(order.pull_events())
        return order_to_dto(order)
