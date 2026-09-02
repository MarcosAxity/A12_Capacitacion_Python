"""Caso de uso: Crear una orden.

Un caso de uso orquesta el flujo de una operación de negocio, pero delega
las reglas de negocio "duras" a las entidades del dominio. Solo depende de
puertos (abstracciones), nunca de detalles concretos de infraestructura.
"""
from __future__ import annotations
from orders.application.dto import CreateOrderRequest, OrderResponse, OrderItemResponse
from orders.application.ports.unit_of_work import UnitOfWork
from orders.domain.entities import Order, OrderItem
from orders.domain.value_objects import Money


class CreateOrderUseCase:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, request: CreateOrderRequest) -> OrderResponse:
        items = [
            OrderItem(
                product_id=i.product_id,
                quantity=i.quantity,
                unit_price=Money(i.unit_price),
            )
            for i in request.items
        ]

        with self._uow as uow:
            order = Order.create(customer_id=request.customer_id, items=items)
            uow.orders.add(order)
            uow.commit()  # persiste y dispara la publicación de OrderCreated

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
