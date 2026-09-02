"""Pruebas unitarias del Aggregate Root Order: cubren reglas de negocio,
transiciones de estado y generación de eventos de dominio.
"""
from decimal import Decimal

import pytest

from orders.domain.entities import Order
from orders.domain.events import OrderCancelled, OrderConfirmed, OrderCreated, OrderItemAdded
from orders.domain.exceptions import (
    EmptyOrderError,
    InvalidItemQuantityError,
    InvalidOrderStateError,
)
from orders.domain.value_objects import OrderStatus, ProductRef


@pytest.mark.unit
class TestOrderCreation:
    def test_create_sets_initial_state(self) -> None:
        order = Order.create(customer_id="cust-1")
        assert order.status == OrderStatus.CREATED
        assert order.items == []
        assert order.customer_id == "cust-1"
        assert order.id  # UUID generado

    def test_create_records_order_created_event(self) -> None:
        order = Order.create(customer_id="cust-1")
        events = order.pull_events()
        assert len(events) == 1
        assert isinstance(events[0], OrderCreated)
        assert events[0].customer_id == "cust-1"

    def test_create_rejects_empty_customer_id(self) -> None:
        with pytest.raises(ValueError, match="customer_id"):
            Order.create(customer_id="   ")

    def test_pull_events_clears_pending_events(self) -> None:
        order = Order.create(customer_id="cust-1")
        order.pull_events()
        assert order.pull_events() == []


@pytest.mark.unit
class TestOrderAddItem:
    def test_add_item_appends_and_records_event(self) -> None:
        order = Order.create(customer_id="cust-1")
        order.pull_events()

        order.add_item(ProductRef("prod-1", "Teclado"), quantity=2, unit_price=Decimal("100"))

        assert len(order.items) == 1
        assert order.items[0].quantity == 2
        events = order.pull_events()
        assert len(events) == 1
        assert isinstance(events[0], OrderItemAdded)

    def test_add_item_rejects_non_positive_quantity(self) -> None:
        order = Order.create(customer_id="cust-1")
        with pytest.raises(InvalidItemQuantityError):
            order.add_item(ProductRef("prod-1", "Teclado"), quantity=0, unit_price=Decimal("10"))

    def test_add_item_rejects_when_order_not_created(self) -> None:
        order = Order.create(customer_id="cust-1")
        order.add_item(ProductRef("prod-1", "Teclado"), quantity=1, unit_price=Decimal("10"))
        order.confirm()

        with pytest.raises(InvalidOrderStateError):
            order.add_item(ProductRef("prod-2", "Mouse"), quantity=1, unit_price=Decimal("10"))


@pytest.mark.unit
class TestOrderTotal:
    def test_total_sums_all_item_subtotals(self) -> None:
        order = Order.create(customer_id="cust-1")
        order.add_item(ProductRef("prod-1", "Teclado"), quantity=2, unit_price=Decimal("100"))
        order.add_item(ProductRef("prod-2", "Mouse"), quantity=1, unit_price=Decimal("50"))

        assert order.total().amount == Decimal("250.00")

    def test_total_is_zero_for_empty_order(self) -> None:
        order = Order.create(customer_id="cust-1")
        assert order.total().amount == Decimal("0.00")


@pytest.mark.unit
class TestOrderConfirm:
    def test_confirm_transitions_state_and_records_event(self) -> None:
        order = Order.create(customer_id="cust-1")
        order.add_item(ProductRef("prod-1", "Teclado"), quantity=1, unit_price=Decimal("100"))
        order.pull_events()

        order.confirm()

        assert order.status == OrderStatus.CONFIRMED
        events = order.pull_events()
        assert len(events) == 1
        assert isinstance(events[0], OrderConfirmed)
        assert events[0].total_amount == Decimal("100.00")

    def test_confirm_rejects_empty_order(self) -> None:
        order = Order.create(customer_id="cust-1")
        with pytest.raises(EmptyOrderError):
            order.confirm()

    def test_confirm_rejects_already_confirmed_order(self) -> None:
        order = Order.create(customer_id="cust-1")
        order.add_item(ProductRef("prod-1", "Teclado"), quantity=1, unit_price=Decimal("100"))
        order.confirm()

        with pytest.raises(InvalidOrderStateError):
            order.confirm()


@pytest.mark.unit
class TestOrderCancel:
    def test_cancel_created_order(self) -> None:
        order = Order.create(customer_id="cust-1")
        order.pull_events()

        order.cancel(reason="cliente se arrepintió")

        assert order.status == OrderStatus.CANCELLED
        events = order.pull_events()
        assert isinstance(events[0], OrderCancelled)
        assert events[0].reason == "cliente se arrepintió"

    def test_cancel_confirmed_order(self) -> None:
        order = Order.create(customer_id="cust-1")
        order.add_item(ProductRef("prod-1", "Teclado"), quantity=1, unit_price=Decimal("100"))
        order.confirm()

        order.cancel()

        assert order.status == OrderStatus.CANCELLED

    def test_cancel_rejects_already_cancelled_order(self) -> None:
        order = Order.create(customer_id="cust-1")
        order.cancel()

        with pytest.raises(InvalidOrderStateError):
            order.cancel()
