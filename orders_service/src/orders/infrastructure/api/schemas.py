"""Esquemas Pydantic (contrato HTTP). Separados de los DTOs de aplicación
para que el dominio y la aplicación no dependan de Pydantic ni de FastAPI.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from orders.application.dto import OrderDTO


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CreateOrderRequest(BaseModel):
    customer_id: str = Field(..., min_length=1, examples=["cust-123"])
    currency: str = Field(default="MXN", min_length=3, max_length=3)


class AddItemRequest(BaseModel):
    product_id: str = Field(..., min_length=1, examples=["prod-001"])
    product_name: str = Field(..., min_length=1, examples=["Teclado mecánico"])
    quantity: int = Field(..., gt=0, examples=[2])
    unit_price: Decimal = Field(..., gt=0, examples=["499.99"])


class CancelOrderRequest(BaseModel):
    reason: str = Field(default="", max_length=500)


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    status: str
    currency: str
    items: list[OrderItemResponse]
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dto(cls, dto: OrderDTO) -> OrderResponse:
        return cls.model_validate(dto)


class ErrorResponse(BaseModel):
    detail: str
    error_type: str


class HealthResponse(BaseModel):
    status: str
    environment: str
