"""Eventos de dominio: hechos relevantes que ocurrieron en el negocio."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
import uuid


@dataclass(frozen=True)
class DomainEvent:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class OrderCreated(DomainEvent):
    """Se emite cuando una orden nueva es creada correctamente."""
    order_id: str = ""
    customer_id: str = ""
    total_amount: Decimal = Decimal(0)
    currency: str = "USD"
