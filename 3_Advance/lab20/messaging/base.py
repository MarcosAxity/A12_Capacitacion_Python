"""Puerto (interfaz) para publicar eventos de dominio en un bus de mensajería.

Siguiendo el mismo enfoque de Inversión de Dependencias del Módulo 12
(Protocol-based DIP), el servidor gRPC depende de esta abstracción y no
de una implementación concreta (RabbitMQ, Redis o Kafka). Esto permite
cambiar de broker sin tocar la lógica de negocio ni el servicio gRPC.
"""
from __future__ import annotations

from typing import Protocol

from generated import orders_pb2


class EventPublisher(Protocol):
    """Puerto de salida (output port) para publicar eventos de dominio."""

    def publish_order_created(self, event: orders_pb2.OrderCreatedEvent) -> None:
        """Publica un evento OrderCreated en el broker configurado."""
        ...

    def close(self) -> None:
        """Libera la conexión con el broker."""
        ...
