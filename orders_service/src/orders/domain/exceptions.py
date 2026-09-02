"""Excepciones del dominio. No conocen HTTP, ORM ni ningún detalle externo.

La capa de infraestructura (API) es responsable de traducirlas a códigos
HTTP apropiados (ver infrastructure/api/error_handlers.py).
"""
from __future__ import annotations


class OrderDomainError(Exception):
    """Excepción base de todas las reglas de negocio de Orders."""


class OrderNotFoundError(OrderDomainError):
    def __init__(self, order_id: str) -> None:
        self.order_id = order_id
        super().__init__(f"Orden '{order_id}' no encontrada")


class EmptyOrderError(OrderDomainError):
    def __init__(self) -> None:
        super().__init__("No se puede confirmar una orden sin items")


class InvalidOrderStateError(OrderDomainError):
    def __init__(self, current: str, target: str) -> None:
        self.current = current
        self.target = target
        super().__init__(f"Transición inválida de estado: '{current}' -> '{target}'")


class InvalidItemQuantityError(OrderDomainError):
    def __init__(self, quantity: int) -> None:
        super().__init__(f"La cantidad debe ser mayor a 0, se recibió {quantity}")


class OrderAlreadyExistsError(OrderDomainError):
    def __init__(self, order_id: str) -> None:
        super().__init__(f"La orden '{order_id}' ya existe")
