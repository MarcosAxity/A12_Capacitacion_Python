"""Endpoints REST de la Orders API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from orders_api.models import Order, OrderCreate
from orders_api.repository import InMemoryOrderRepository, OrderNotFoundError

router = APIRouter(prefix="/orders", tags=["orders"])
_repo = InMemoryOrderRepository()


@router.post("", response_model=Order, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate) -> Order:
    order = Order(**payload.model_dump())
    return _repo.add(order)


@router.get("", response_model=list[Order])
def list_orders() -> list[Order]:
    return _repo.list()


@router.get("/{order_id}", response_model=Order)
def get_order(order_id: UUID) -> Order:
    try:
        return _repo.get(order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Pedido no encontrado") from exc


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: UUID) -> None:
    try:
        _repo.delete(order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Pedido no encontrado") from exc
