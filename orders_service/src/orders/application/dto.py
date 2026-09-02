"""DTOs de la capa de aplicación.

Son distintos de los esquemas Pydantic de la API: estos son simples
dataclasses, sin dependencia de FastAPI/Pydantic, para que la capa de
aplicación siga siendo independiente del framework web.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class OrderItemDTO:
    product_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


@dataclass(frozen=True, slots=True)
class OrderDTO:
    id: str
    customer_id: str
    status: str
    currency: str
    items: list[OrderItemDTO]
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class CreateOrderInput:
    customer_id: str
    currency: str = "MXN"


@dataclass(frozen=True, slots=True)
class AddItemInput:
    order_id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
