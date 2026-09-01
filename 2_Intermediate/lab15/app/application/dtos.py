"""
DTOs (Data Transfer Objects) vs ENTIDADES.

- Las ENTIDADES (app/domain/entities.py) contienen comportamiento y
  reglas de negocio (ej. Order.confirm(), validaciones en __post_init__).
- Los DTOs son estructuras "planas", sin lógica, que sirven para
  entrar/salir de la capa de aplicación. Desacoplan la forma en la que
  el "mundo exterior" (API REST, CLI, mensajería) habla con los casos
  de uso, de la forma interna en que el dominio modela sus objetos.

Esto permite, por ejemplo, cambiar el schema de la API pública sin tocar
el dominio, o exponer únicamente los campos que queremos exponer.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class OrderItemDTO:
    product_id: str
    quantity: int
    unit_price: Decimal


@dataclass(frozen=True)
class CreateOrderInputDTO:
    customer_id: str
    items: list[OrderItemDTO]


@dataclass(frozen=True)
class OrderOutputDTO:
    id: str
    customer_id: str
    status: str
    total: Decimal
    items: list[OrderItemDTO]
