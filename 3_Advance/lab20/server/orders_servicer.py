"""Implementación del servicio gRPC OrdersService.

El servicer depende únicamente del puerto EventPublisher (Protocol), nunca
de una librería concreta de mensajería: es la misma Inversión de
Dependencias aplicada en el Módulo 12 y en el Módulo 16 (Clean Architecture),
ahora en el borde de un servicio gRPC.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

import grpc

from generated import orders_pb2, orders_pb2_grpc
from messaging.base import EventPublisher

logger = logging.getLogger(__name__)


class OrdersServicer(orders_pb2_grpc.OrdersServiceServicer):
    """Servicer gRPC con un repositorio en memoria (thread-safe no requerido
    para esta demo; en producción se inyectaría un repositorio real, igual
    que los adapters del Módulo 16)."""

    def __init__(self, publisher: EventPublisher) -> None:
        self._publisher = publisher
        self._orders: dict[str, orders_pb2.Order] = {}

    def CreateOrder(self, request: orders_pb2.CreateOrderRequest, context: grpc.ServicerContext):
        if not request.items:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "La orden debe tener al menos un item")

        total = sum(item.quantity * item.unit_price for item in request.items)
        order = orders_pb2.Order(
            order_id=str(uuid.uuid4()),
            customer_id=request.customer_id,
            items=request.items,
            total_amount=total,
            status="CONFIRMED",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._orders[order.order_id] = order
        logger.info("Orden creada: %s (total=%.2f)", order.order_id, total)

        event = orders_pb2.OrderCreatedEvent(
            event_id=str(uuid.uuid4()),
            order_id=order.order_id,
            customer_id=order.customer_id,
            total_amount=order.total_amount,
            occurred_at=order.created_at,
        )
        self._publisher.publish_order_created(event)

        return orders_pb2.CreateOrderResponse(order=order)

    def GetOrder(self, request: orders_pb2.GetOrderRequest, context: grpc.ServicerContext):
        order = self._orders.get(request.order_id)
        if order is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"Orden {request.order_id} no encontrada")
        return orders_pb2.GetOrderResponse(order=order)

    def ListOrders(self, request: orders_pb2.ListOrdersRequest, context: grpc.ServicerContext):
        return orders_pb2.ListOrdersResponse(orders=list(self._orders.values()))
