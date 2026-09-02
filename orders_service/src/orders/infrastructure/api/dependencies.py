"""Dependencias de FastAPI: construyen, por cada request, los casos de uso
a partir del AppContainer (composition root) y del puerto UnitOfWork.
Esto mantiene los routers desacoplados de los adaptadores concretos.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request

from orders.application.use_cases import (
    AddItemToOrderUseCase,
    CancelOrderUseCase,
    ConfirmOrderUseCase,
    CreateOrderUseCase,
    GetOrderUseCase,
    ListOrdersUseCase,
)
from orders.infrastructure.adapters.db.unit_of_work import SqlAlchemyUnitOfWork
from orders.infrastructure.api.security import get_current_user  # noqa: F401  (re-exported)
from orders.infrastructure.composition_root import AppContainer


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


async def get_uow(
    container: Annotated[AppContainer, Depends(get_container)],
) -> AsyncGenerator[SqlAlchemyUnitOfWork, None]:
    async with SqlAlchemyUnitOfWork(container.session_factory) as uow:
        yield uow


async def get_create_order_use_case(
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)],
    container: Annotated[AppContainer, Depends(get_container)],
) -> AsyncGenerator[CreateOrderUseCase, None]:
    yield CreateOrderUseCase(repository=uow.orders, event_publisher=container.event_publisher)
    await uow.commit()


async def get_add_item_use_case(
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)],
    container: Annotated[AppContainer, Depends(get_container)],
) -> AsyncGenerator[AddItemToOrderUseCase, None]:
    yield AddItemToOrderUseCase(repository=uow.orders, event_publisher=container.event_publisher)
    await uow.commit()


async def get_confirm_order_use_case(
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)],
    container: Annotated[AppContainer, Depends(get_container)],
) -> AsyncGenerator[ConfirmOrderUseCase, None]:
    yield ConfirmOrderUseCase(repository=uow.orders, event_publisher=container.event_publisher)
    await uow.commit()


async def get_cancel_order_use_case(
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)],
    container: Annotated[AppContainer, Depends(get_container)],
) -> AsyncGenerator[CancelOrderUseCase, None]:
    yield CancelOrderUseCase(repository=uow.orders, event_publisher=container.event_publisher)
    await uow.commit()


async def get_get_order_use_case(
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)],
) -> AsyncGenerator[GetOrderUseCase, None]:
    yield GetOrderUseCase(repository=uow.orders)


async def get_list_orders_use_case(
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)],
) -> AsyncGenerator[ListOrdersUseCase, None]:
    yield ListOrdersUseCase(repository=uow.orders)
