"""Router HTTP de Orders. Traduce requests/responses HTTP a llamadas a
casos de uso de la capa de aplicación. No contiene lógica de negocio.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from orders.application.dto import AddItemInput, CreateOrderInput
from orders.application.use_cases import (
    AddItemToOrderUseCase,
    CancelOrderUseCase,
    ConfirmOrderUseCase,
    CreateOrderUseCase,
    GetOrderUseCase,
    ListOrdersUseCase,
)
from orders.infrastructure.api.dependencies import (
    get_add_item_use_case,
    get_cancel_order_use_case,
    get_confirm_order_use_case,
    get_create_order_use_case,
    get_get_order_use_case,
    get_list_orders_use_case,
)
from orders.infrastructure.api.schemas import (
    AddItemRequest,
    CancelOrderRequest,
    CreateOrderRequest,
    OrderResponse,
)
from orders.infrastructure.api.security import get_current_user

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: CreateOrderRequest,
    use_case: Annotated[CreateOrderUseCase, Depends(get_create_order_use_case)],
) -> OrderResponse:
    """Crea una nueva orden vacía para un cliente."""
    dto = await use_case.execute(
        CreateOrderInput(customer_id=payload.customer_id, currency=payload.currency)
    )
    return OrderResponse.from_dto(dto)


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    use_case: Annotated[ListOrdersUseCase, Depends(get_list_orders_use_case)],
    customer_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[OrderResponse]:
    """Lista órdenes, con filtro opcional por cliente y paginación."""
    dtos = await use_case.execute(customer_id=customer_id, limit=limit, offset=offset)
    return [OrderResponse.from_dto(d) for d in dtos]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    use_case: Annotated[GetOrderUseCase, Depends(get_get_order_use_case)],
) -> OrderResponse:
    """Obtiene el detalle de una orden por id."""
    dto = await use_case.execute(order_id)
    return OrderResponse.from_dto(dto)


@router.post("/{order_id}/items", response_model=OrderResponse)
async def add_item(
    order_id: str,
    payload: AddItemRequest,
    use_case: Annotated[AddItemToOrderUseCase, Depends(get_add_item_use_case)],
) -> OrderResponse:
    """Agrega un item a una orden en estado 'created'."""
    dto = await use_case.execute(
        AddItemInput(
            order_id=order_id,
            product_id=payload.product_id,
            product_name=payload.product_name,
            quantity=payload.quantity,
            unit_price=payload.unit_price,
        )
    )
    return OrderResponse.from_dto(dto)


@router.post("/{order_id}/confirm", response_model=OrderResponse)
async def confirm_order(
    order_id: str,
    use_case: Annotated[ConfirmOrderUseCase, Depends(get_confirm_order_use_case)],
) -> OrderResponse:
    """Confirma una orden (requiere al menos un item)."""
    dto = await use_case.execute(order_id)
    return OrderResponse.from_dto(dto)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: str,
    payload: CancelOrderRequest,
    use_case: Annotated[CancelOrderUseCase, Depends(get_cancel_order_use_case)],
) -> OrderResponse:
    """Cancela una orden en estado 'created' o 'confirmed'."""
    dto = await use_case.execute(order_id, reason=payload.reason)
    return OrderResponse.from_dto(dto)
