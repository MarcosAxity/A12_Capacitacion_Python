"""Composition root: único lugar del sistema que conoce TODAS las capas a
la vez (dominio, aplicación e infraestructura) y las conecta entre sí.

En una app real, este archivo se parecería a la función de arranque de
FastAPI/Django/Flask (o a un contenedor de inyección de dependencias).
"""
from __future__ import annotations

from orders.application.event_handlers.order_created_handlers import send_order_confirmation
from orders.application.use_cases.create_order import CreateOrderUseCase
from orders.application.use_cases.get_order import GetOrderUseCase
from orders.application.use_cases.list_orders import ListOrdersUseCase
from orders.domain.events import OrderCreated
from orders.infrastructure.events.in_memory_event_bus import InMemoryEventBus
from orders.infrastructure.persistence.in_memory_repository import InMemoryOrderRepository
from orders.infrastructure.persistence.in_memory_unit_of_work import InMemoryUnitOfWork
from orders.interfaces.controllers.order_controller import OrderController
from orders.interfaces.presenters.order_presenter import OrderPresenter


def build_controller() -> OrderController:
    repository = InMemoryOrderRepository()

    event_bus = InMemoryEventBus()
    event_bus.subscribe(OrderCreated, send_order_confirmation)

    uow = InMemoryUnitOfWork(repository, event_bus)

    create_order_uc = CreateOrderUseCase(uow)
    get_order_uc = GetOrderUseCase(uow)
    list_orders_uc = ListOrdersUseCase(uow)

    presenter = OrderPresenter()

    return OrderController(create_order_uc, get_order_uc, list_orders_uc, presenter)
