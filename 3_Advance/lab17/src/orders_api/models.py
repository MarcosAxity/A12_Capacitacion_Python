"""Modelos Pydantic para la Orders API."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, PositiveFloat, PositiveInt


class OrderStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class OrderCreate(BaseModel):
    customer: str = Field(min_length=1, max_length=120)
    item: str = Field(min_length=1, max_length=120)
    quantity: PositiveInt
    unit_price: PositiveFloat


class Order(OrderCreate):
    id: UUID = Field(default_factory=uuid4)
    status: OrderStatus = OrderStatus.PENDING

    @property
    def total(self) -> float:
        return round(self.quantity * self.unit_price, 2)


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
