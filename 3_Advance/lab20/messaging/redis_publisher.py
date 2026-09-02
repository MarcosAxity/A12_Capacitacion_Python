"""Adaptador de mensajería para Redis, vía redis-py (Pub/Sub).

Alternativa ligera a RabbitMQ para notificaciones de eventos "fire and
forget". El mismo evento OrderCreatedEvent se serializa en Protobuf y se
publica en el canal "order.created". Si se necesitara persistencia/replay
de eventos, se recomendaría usar Redis Streams (XADD) en vez de Pub/Sub.
"""
from __future__ import annotations

import logging

import redis

from generated import orders_pb2

logger = logging.getLogger(__name__)

CHANNEL_NAME = "order.created"


class RedisPublisher:
    """Publica eventos de dominio en un canal de Redis Pub/Sub."""

    def __init__(self, client: "redis.Redis | None" = None, url: str = "redis://localhost:6379/0") -> None:
        # Se acepta un cliente inyectado (p. ej. fakeredis en tests) para
        # respetar la inversión de dependencias y facilitar el testeo.
        self._client = client or redis.Redis.from_url(url)

    def publish_order_created(self, event: orders_pb2.OrderCreatedEvent) -> None:
        body = event.SerializeToString()
        self._client.publish(CHANNEL_NAME, body)
        logger.info("Evento OrderCreated publicado en Redis (order_id=%s)", event.order_id)

    def close(self) -> None:
        self._client.close()
