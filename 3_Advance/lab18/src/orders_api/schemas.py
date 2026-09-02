"""Esquemas Pydantic para la API de Orders (in-memory, uso educativo)."""
from __future__ import annotations

from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    customer: str = Field(..., min_length=1, description="Nombre del cliente")
    items: List[str] = Field(..., min_length=1, description="Items de la orden")
    total: float = Field(..., ge=0, description="Total de la orden")


class OrderOut(BaseModel):
    id: str
    customer: str
    items: List[str]
    total: float
    status: str = "pending"


def new_order(data: OrderCreate) -> OrderOut:
    return OrderOut(id=str(uuid4()), customer=data.customer, items=data.items, total=data.total)
