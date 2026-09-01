"""Entidades de dominio.

SRP: este módulo tiene una única razón de cambio: la forma/estructura
del pedido (Order). No sabe nada de persistencia, notificaciones ni
descuentos.
"""

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    DISCOUNTED = "DISCOUNTED"
    NOTIFIED = "NOTIFIED"


@dataclass
class Order:
    customer: str
    total: float
    id: str = field(default_factory=lambda: str(uuid4()))
    status: OrderStatus = OrderStatus.CREATED

    def __post_init__(self) -> None:
        if self.total < 0:
            raise ValueError("El total del pedido no puede ser negativo")
