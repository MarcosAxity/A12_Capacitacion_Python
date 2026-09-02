"""Eventos de dominio: hechos inmutables que ocurrieron en el pasado.

Se acumulan en el Aggregate Root (Order) y son publicados por la capa de
aplicación después de persistir, vía el puerto EventPublisher.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class DomainEvent:
    order_id: str
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


@dataclass(frozen=True, slots=True)
class OrderCreated(DomainEvent):
    customer_id: str = ""


@dataclass(frozen=True, slots=True)
class OrderItemAdded(DomainEvent):
    product_id: str = ""
    quantity: int = 0
    unit_price: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class OrderConfirmed(DomainEvent):
    total_amount: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class OrderCancelled(DomainEvent):
    reason: str = ""
