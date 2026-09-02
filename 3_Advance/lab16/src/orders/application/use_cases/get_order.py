"""Caso de uso: Consultar una orden por id."""
from __future__ import annotations
from orders.application.dto import OrderResponse, OrderItemResponse
from orders.application.ports.unit_of_work import UnitOfWork
from orders.domain.entities import Order
from orders.domain.exceptions import OrderNotFoundError


class GetOrderUseCase:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, order_id: str) -> OrderResponse:
        with self._uow as uow:
            order = uow.orders.get(order_id)
            if order is None:
                raise OrderNotFoundError(f"Orden {order_id} no encontrada.")
            return _to_response(order)


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
