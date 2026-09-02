"""Pruebas específicas del Unit of Work: verifican que los eventos de
dominio SOLO se publiquen cuando hay un commit() explícito."""
from decimal import Decimal

from orders.domain.entities import Order, OrderItem
from orders.domain.events import OrderCreated
from orders.domain.value_objects import Money
from orders.infrastructure.events.in_memory_event_bus import InMemoryEventBus
from orders.infrastructure.persistence.in_memory_repository import InMemoryOrderRepository
from orders.infrastructure.persistence.in_memory_unit_of_work import InMemoryUnitOfWork


def build_uow():
    repo = InMemoryOrderRepository()
    bus = InMemoryEventBus()
    published = []
    bus.subscribe(OrderCreated, lambda e: published.append(e))
    return InMemoryUnitOfWork(repo, bus), published


def test_events_are_not_published_without_commit():
    uow, published = build_uow()
    order = Order.create(customer_id="c1", items=[OrderItem("p1", 1, Money(Decimal("1.00")))])

    with uow as u:
        u.orders.add(order)
        # commit() NO se llama a propósito

    assert published == []


def test_events_are_published_after_commit():
    uow, published = build_uow()
    order = Order.create(customer_id="c1", items=[OrderItem("p1", 1, Money(Decimal("1.00")))])

    with uow as u:
        u.orders.add(order)
        u.commit()

    assert len(published) == 1
    assert published[0].order_id == order.id
