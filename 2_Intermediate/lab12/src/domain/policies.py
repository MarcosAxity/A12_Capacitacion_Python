"""Estrategias de descuento.

OCP (Open/Closed Principle):
    `OrderService` depende únicamente del puerto `DiscountPolicy`.
    Para agregar una nueva forma de descontar (ej. `SeasonalDiscount`)
    NO se modifica `OrderService` ni las políticas existentes: se crea
    una clase nueva que cumple el mismo Protocol. El módulo está
    "abierto a extensión, cerrado a modificación".
"""

from dataclasses import dataclass


class NoDiscount:
    """Política neutra: no aplica ningún descuento."""

    def apply(self, total: float) -> float:
        return total


@dataclass
class PercentageDiscount:
    """Descuento porcentual, ej. 10% -> percentage=0.10."""

    percentage: float

    def __post_init__(self) -> None:
        if not 0 <= self.percentage <= 1:
            raise ValueError("percentage debe estar entre 0 y 1")

    def apply(self, total: float) -> float:
        return round(total * (1 - self.percentage), 2)


@dataclass
class FixedAmountDiscount:
    """Descuento de monto fijo, nunca deja el total por debajo de 0."""

    amount: float

    def apply(self, total: float) -> float:
        return max(0.0, round(total - self.amount, 2))


# Ejemplo de EXTENSIÓN sin tocar lo anterior (nueva funcionalidad, OCP):
@dataclass
class ThresholdDiscount:
    """Aplica un descuento porcentual solo si se supera un umbral."""

    threshold: float
    percentage: float

    def apply(self, total: float) -> float:
        if total >= self.threshold:
            return round(total * (1 - self.percentage), 2)
        return total
