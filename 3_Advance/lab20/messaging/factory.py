"""Factory/provider para construir el EventPublisher activo.

Mismo patrón factory/provider usado en el Módulo 12 (SOLID): el resto de la
aplicación pide "un publisher" sin saber si detrás hay RabbitMQ, Redis o un
stub en memoria. El backend se selecciona por variable de entorno, lo que
permite cambiar de broker en tiempo de despliegue sin recompilar código.
"""
from __future__ import annotations

import os

from messaging.base import EventPublisher
from messaging.in_memory_publisher import InMemoryPublisher
from messaging.rabbitmq_publisher import RabbitMQPublisher
from messaging.redis_publisher import RedisPublisher

VALID_BACKENDS = {"rabbitmq", "redis", "memory"}


def get_publisher(backend: str | None = None) -> EventPublisher:
    """Devuelve la implementación de EventPublisher configurada.

    Args:
        backend: "rabbitmq" | "redis" | "memory". Si es None, se lee de la
            variable de entorno MESSAGING_BACKEND (default: "memory").
    """
    backend = (backend or os.getenv("MESSAGING_BACKEND", "memory")).lower()
    if backend not in VALID_BACKENDS:
        raise ValueError(f"Backend de mensajería no soportado: {backend!r}")

    if backend == "rabbitmq":
        url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F")
        return RabbitMQPublisher(url=url)
    if backend == "redis":
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        return RedisPublisher(url=url)
    return InMemoryPublisher()
