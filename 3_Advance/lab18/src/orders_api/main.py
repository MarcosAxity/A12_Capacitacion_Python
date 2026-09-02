"""API mínima de Orders usada como backend para el CLI del Módulo 18.

Es una API en memoria (sin base de datos) cuyo único propósito es dar al
CLI (Typer) y a los scripts de mantenimiento (argparse/click) un endpoint
real contra el cual operar. En un proyecto real, esta API sería el
servicio de Órdenes construido en el Módulo 16 (Clean Architecture).
"""
from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi import status as http_status

from .schemas import OrderCreate, OrderOut, new_order

app = FastAPI(title="Orders API", version="1.0.0")

# Almacén en memoria: id -> OrderOut
_DB: Dict[str, OrderOut] = {}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "orders_count": len(_DB)}


@app.get("/orders", response_model=List[OrderOut])
def list_orders(status: Optional[str] = None) -> List[OrderOut]:
    orders = list(_DB.values())
    if status:
        orders = [o for o in orders if o.status == status]
    return orders


@app.post("/orders", response_model=OrderOut, status_code=http_status.HTTP_201_CREATED)
def create_order(payload: OrderCreate) -> OrderOut:
    order = new_order(payload)
    _DB[order.id] = order
    return order


@app.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: str) -> OrderOut:
    order = _DB.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return order


@app.delete("/orders/{order_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_order(order_id: str) -> None:
    if order_id not in _DB:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    del _DB[order_id]


def _reset_db() -> None:
    """Utilidad interna para tests: limpia el almacén en memoria."""
    _DB.clear()
