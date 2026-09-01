"""
Adaptador de entrada (driving adapter): API HTTP con FastAPI.

Este archivo es donde el "mundo exterior" entra al hexágono. Sus
responsabilidades son SOLO:
  1. Recibir/validar el request HTTP (Pydantic).
  2. Traducirlo a un DTO de aplicación.
  3. Invocar el caso de uso correspondiente.
  4. Traducir el DTO de salida a una respuesta HTTP.

NINGUNA regla de negocio vive aquí.
"""

from __future__ import annotations

import os

from app.api.schemas import CreateOrderRequest, OrderItemOut, OrderResponse
from app.application.dtos import CreateOrderInputDTO, OrderItemDTO
from app.application.use_cases import CreateOrderUseCase, GetOrderUseCase
from app.container import Container
from app.domain.exceptions import DomainError, OrderNotFoundError
from fastapi import Depends, FastAPI, HTTPException

app = FastAPI(title="Orders API — Arquitectura Hexagonal", version="1.0.0")

# Wiring: un único contenedor compartido por la app. Con la variable de
# entorno USE_SQLALCHEMY=1 se puede cambiar el adaptador de persistencia
# de "memoria" a "SQLAlchemy/SQLite" sin tocar ninguna otra línea.
_container = Container(use_sqlalchemy=os.getenv("USE_SQLALCHEMY") == "1")


def get_create_order_use_case() -> CreateOrderUseCase:
    return _container.create_order_use_case


def get_get_order_use_case() -> GetOrderUseCase:
    return _container.get_order_use_case


@app.post("/orders", response_model=OrderResponse, status_code=201)
def create_order(
    request: CreateOrderRequest,
    use_case: CreateOrderUseCase = Depends(get_create_order_use_case),
) -> OrderResponse:
    input_dto = CreateOrderInputDTO(
        customer_id=request.customer_id,
        items=[
            OrderItemDTO(
                product_id=i.product_id, quantity=i.quantity, unit_price=i.unit_price
            )
            for i in request.items
        ],
    )
    try:
        output = use_case.execute(input_dto)
    except DomainError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return _to_response(output)


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str,
    use_case: GetOrderUseCase = Depends(get_get_order_use_case),
) -> OrderResponse:
    try:
        output = use_case.execute(order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return _to_response(output)


def _to_response(output) -> OrderResponse:
    return OrderResponse(
        id=output.id,
        customer_id=output.customer_id,
        status=output.status,
        total=output.total,
        items=[
            OrderItemOut(
                product_id=i.product_id, quantity=i.quantity, unit_price=i.unit_price
            )
            for i in output.items
        ],
    )
