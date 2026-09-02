"""Value Objects del dominio de Orders.

Un Value Object es inmutable y se compara por valor, no por identidad.
No dependen de infraestructura alguna (sin ORM, sin FastAPI, sin nada externo).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum


class DomainValidationError(ValueError):
    """Error base para violaciones de invariantes del dominio."""


@dataclass(frozen=True, slots=True)
class Money:
    """Representa un monto monetario. Siempre en la moneda indicada.

    Se usa Decimal (nunca float) para evitar errores de redondeo binario
    en cálculos financieros.
    """

    amount: Decimal
    currency: str = "MXN"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise DomainValidationError("El monto no puede ser negativo")
        if len(self.currency) != 3:
            raise DomainValidationError("La moneda debe ser un código ISO 4217 de 3 letras")
        quantized = self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        object.__setattr__(self, "amount", quantized)
        object.__setattr__(self, "currency", self.currency.upper())

    def __add__(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, factor: int) -> Money:
        if factor < 0:
            raise DomainValidationError("El factor no puede ser negativo")
        return Money(self.amount * factor, self.currency)

    def _assert_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise DomainValidationError(
                "No se pueden operar montos en distinta moneda: "
                f"{self.currency} vs {other.currency}"
            )

    @classmethod
    def zero(cls, currency: str = "MXN") -> Money:
        return cls(Decimal("0"), currency)


def new_order_id() -> str:
    return str(uuid.uuid4())


class OrderStatus(str, Enum):
    """Estados posibles de una orden y sus transiciones válidas."""

    CREATED = "created"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

    def can_transition_to(self, target: OrderStatus) -> bool:
        allowed = {
            OrderStatus.CREATED: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
            OrderStatus.CONFIRMED: {OrderStatus.CANCELLED},
            OrderStatus.CANCELLED: set(),
        }
        return target in allowed[self]


@dataclass(frozen=True, slots=True)
class ProductRef:
    """Referencia a un producto externo (no es una entidad del propio dominio)."""

    product_id: str
    name: str

    def __post_init__(self) -> None:
        if not self.product_id.strip():
            raise DomainValidationError("product_id no puede estar vacío")
        if not self.name.strip():
            raise DomainValidationError("El nombre del producto no puede estar vacío")
