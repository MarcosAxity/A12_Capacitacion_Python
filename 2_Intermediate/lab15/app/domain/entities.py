"""
Capa de DOMINIO.

Aquí viven las reglas de negocio puras. Este módulo NO debe importar
nada de FastAPI, SQLAlchemy, requests, etc. Si algún día cambiamos
la base de datos o el framework web, este archivo no se toca.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from app.domain.exceptions import EmptyOrderError, InvalidQuantityError


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class OrderItem:
    """Value object: una línea de pedido."""

    product_id: str
    quantity: int
    unit_price: Decimal

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise InvalidQuantityError(
                f"La cantidad debe ser mayor a 0 (producto={self.product_id})"
            )
        if self.unit_price < 0:
            raise InvalidQuantityError(
                f"El precio unitario no puede ser negativo (producto={self.product_id})"
            )

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass
class Order:
    """
    Entidad raíz (Aggregate Root) del dominio de pedidos.

    Toda la lógica de negocio relacionada al ciclo de vida de un pedido
    vive aquí, y no en un endpoint ni en un repositorio.
    """

    customer_id: str
    items: list[OrderItem]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: OrderStatus = OrderStatus.CREATED

    def __post_init__(self) -> None:
        if not self.items:
            raise EmptyOrderError("Un pedido debe tener al menos un item")

    @property
    def total(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal("0"))

    def confirm(self) -> None:
        if self.status != OrderStatus.CREATED:
            raise ValueError(f"No se puede confirmar un pedido en estado {self.status}")
        self.status = OrderStatus.CONFIRMED

    def cancel(self) -> None:
        if self.status == OrderStatus.CANCELLED:
            return
        self.status = OrderStatus.CANCELLED
