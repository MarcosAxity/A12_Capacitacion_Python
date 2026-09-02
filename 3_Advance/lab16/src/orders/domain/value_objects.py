"""Value Objects del dominio: objetos sin identidad, definidos por su valor."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class Money:
    """Representa una cantidad monetaria. Inmutable (frozen) y con reglas
    propias de validación, típico de un Value Object en DDD."""

    amount: Decimal
    currency: str = "USD"

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))
        if self.amount < 0:
            raise ValueError("El monto no puede ser negativo.")

    def multiply(self, factor: int) -> "Money":
        return Money(self.amount * factor, self.currency)

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
