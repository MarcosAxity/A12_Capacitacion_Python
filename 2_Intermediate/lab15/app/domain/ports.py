"""
PUERTOS (Ports).

Un puerto es un contrato que el dominio/aplicación necesita para funcionar,
pero cuya implementación concreta (SQL, HTTP, memoria, colas, etc.) no le
importa. Se definen como `typing.Protocol` para lograr "duck typing"
estático: cualquier clase que implemente estos métodos, sin necesidad de
heredar explícitamente, cumple el contrato (principio de inversión de
dependencias: el dominio define la interfaz, la infraestructura la obedece).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.entities import Order


@runtime_checkable
class OrderRepositoryPort(Protocol):
    """Puerto de salida (driven port) para persistir/leer pedidos."""

    def save(self, order: Order) -> None:
        """Guarda (crea o actualiza) un pedido."""
        ...

    def get_by_id(self, order_id: str) -> Order | None:
        """Recupera un pedido por id, o None si no existe."""
        ...

    def list_all(self) -> list[Order]:
        """Lista todos los pedidos almacenados."""
        ...


@runtime_checkable
class NotificationPort(Protocol):
    """Puerto de salida para notificar eventos de negocio hacia afuera."""

    def notify_order_created(self, order: Order) -> None:
        """Notifica que un pedido fue creado (ej. vía HTTP/Webhook/cola)."""
        ...
