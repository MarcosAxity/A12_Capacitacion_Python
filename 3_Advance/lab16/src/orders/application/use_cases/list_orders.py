"""Caso de uso: Listar todas las órdenes."""
from __future__ import annotations
from typing import List
from orders.application.dto import OrderResponse, OrderItemResponse
from orders.application.ports.unit_of_work import UnitOfWork
from orders.domain.entities import Order


class ListOrdersUseCase:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self) -> List[OrderResponse]:
        with self._uow as uow:
            return [_to_response(o) for o in uow.orders.list()]


def _to_response(order: Order) -> OrderResponse:
    total = order.total()
    return OrderResponse(
        id=order.id,
        customer_id=order.customer_id,
        status=order.status.value,
        items=[
            OrderItemResponse(
                product_id=i.product_id,
                quantity=i.quantity,
                unit_price=i.unit_price.amount,
                subtotal=i.subtotal().amount,
            )
            for i in order.items
        ],
        total_amount=total.amount,
        currency=total.currency,
    )
