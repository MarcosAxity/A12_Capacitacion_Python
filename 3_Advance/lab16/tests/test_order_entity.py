"""Pruebas unitarias del dominio: no requieren infraestructura ni mocks
elaborados, sólo objetos Python puros. Esto es una señal de buen diseño."""
from decimal import Decimal

import pytest

from orders.domain.entities import Order, OrderItem
from orders.domain.events import OrderCreated
from orders.domain.exceptions import EmptyOrderError, InvalidOrderStateError
from orders.domain.value_objects import Money


def make_item(price="10.00", qty=2):
    return OrderItem(product_id="p1", quantity=qty, unit_price=Money(Decimal(price)))


def test_order_cannot_be_created_without_items():
    with pytest.raises(EmptyOrderError):
        Order.create(customer_id="c1", items=[])


def test_order_total_is_sum_of_item_subtotals():
    order = Order.create(customer_id="c1", items=[make_item("10.00", 2), make_item("5.00", 1)])
    assert order.total().amount == Decimal("25.00")


def test_order_create_registers_order_created_event():
    order = Order.create(customer_id="c1", items=[make_item()])
    events = order.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], OrderCreated)
    assert events[0].order_id == order.id
    assert events[0].total_amount == order.total().amount


def test_pull_domain_events_clears_pending_events():
    order = Order.create(customer_id="c1", items=[make_item()])
    order.pull_domain_events()
    assert order.pull_domain_events() == []


def test_cannot_cancel_an_already_cancelled_order():
    order = Order.create(customer_id="c1", items=[make_item()])
    order.cancel()
    with pytest.raises(InvalidOrderStateError):
        order.cancel()
