"""
Schemas de Pydantic para la API HTTP.

Son otra forma de DTO, específica para el "adaptador de entrada" HTTP
(FastAPI). Se traducen a los DTOs de aplicación antes de invocar los
casos de uso, para que la capa de aplicación no dependa de Pydantic ni
de FastAPI.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class OrderItemIn(BaseModel):
    product_id: str = Field(..., examples=["SKU-001"])
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)


class CreateOrderRequest(BaseModel):
    customer_id: str = Field(..., examples=["cust-123"])
    items: list[OrderItemIn]


class OrderItemOut(BaseModel):
    product_id: str
    quantity: int
    unit_price: Decimal


class OrderResponse(BaseModel):
    id: str
    customer_id: str
    status: str
    total: Decimal
    items: list[OrderItemOut]
