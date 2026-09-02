"""Funciones puras para mapear entidades de dominio a DTOs de aplicación."""
from __future__ import annotations

from orders.application.dto import OrderDTO, OrderItemDTO
from orders.domain.entities import Order


def order_to_dto(order: Order) -> OrderDTO:
    return OrderDTO(
        id=order.id,
        customer_id=order.customer_id,
        status=order.status.value,
        currency=order.currency,
        items=[
            OrderItemDTO(
                product_id=item.product.product_id,
                product_name=item.product.name,
                quantity=item.quantity,
                unit_price=item.unit_price.amount,
                subtotal=item.subtotal.amount,
            )
            for item in order.items
        ],
        total_amount=order.total().amount,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )
