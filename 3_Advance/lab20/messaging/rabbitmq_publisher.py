"""Adaptador de mensajería para RabbitMQ (protocolo AMQP), vía pika.

Publica el evento OrderCreatedEvent serializado en Protobuf binario en un
exchange topic llamado "orders", con routing key "order.created". Cualquier
consumidor (otro servicio, otro lenguaje) que entienda el contrato .proto
puede deserializar el mensaje sin acoplarse a Python.
"""
from __future__ import annotations

import logging

import pika

from generated import orders_pb2

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "orders"
ROUTING_KEY = "order.created"


class RabbitMQPublisher:
    """Publica eventos de dominio en RabbitMQ."""

    def __init__(self, url: str = "amqp://guest:guest@localhost:5672/%2F") -> None:
        self._url = url
        self._connection: pika.BlockingConnection | None = None
        self._channel = None

    def _ensure_connection(self) -> None:
        if self._connection is not None and self._connection.is_open:
            return
        self._connection = pika.BlockingConnection(pika.URLParameters(self._url))
        self._channel = self._connection.channel()
        self._channel.exchange_declare(
            exchange=EXCHANGE_NAME, exchange_type="topic", durable=True
        )

    def publish_order_created(self, event: orders_pb2.OrderCreatedEvent) -> None:
        self._ensure_connection()
        body = event.SerializeToString()
        self._channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY,
            body=body,
            properties=pika.BasicProperties(
                content_type="application/x-protobuf",
                delivery_mode=2,  # mensaje persistente
            ),
        )
        logger.info("Evento OrderCreated publicado en RabbitMQ (order_id=%s)", event.order_id)

    def close(self) -> None:
        if self._connection is not None and self._connection.is_open:
            self._connection.close()
