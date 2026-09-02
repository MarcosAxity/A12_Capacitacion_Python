"""DTOs (Data Transfer Objects) de la capa de aplicación.

Son estructuras de datos "planas" que entran y salen de los casos de uso.
Desacoplan el dominio (Entidades/Value Objects) de los formatos externos
(JSON, dicts de HTTP, filas de CLI, etc.).
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import List


@dataclass
class CreateOrderItemRequest:
    product_id: str
    quantity: int
    unit_price: Decimal


@dataclass
class CreateOrderRequest:
    customer_id: str
    items: List[CreateOrderItemRequest]


@dataclass
class OrderItemResponse:
    product_id: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


@dataclass
class OrderResponse:
    id: str
    customer_id: str
    status: str
    items: List[OrderItemResponse]
    total_amount: Decimal
    currency: str
