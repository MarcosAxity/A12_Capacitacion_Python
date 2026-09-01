"""
PRUEBAS DE DOMINIO.

No usan FastAPI, ni base de datos, ni ningún adaptador: solo importan
`app.domain`. Son las más rápidas y las que validan las reglas de
negocio "puras". Si un día cambiamos de FastAPI a Flask, o de SQLite a
Postgres, estas pruebas NO deberían romperse.
"""

from decimal import Decimal

import pytest
from app.domain.entities import Order, OrderItem, OrderStatus
from app.domain.exceptions import EmptyOrderError, InvalidQuantityError


def test_order_total_sums_all_items():
    order = Order(
        customer_id="cust-1",
        items=[
            OrderItem(product_id="A", quantity=2, unit_price=Decimal("10.00")),
            OrderItem(product_id="B", quantity=1, unit_price=Decimal("5.50")),
        ],
    )

    assert order.total == Decimal("25.50")
    assert order.status == OrderStatus.CREATED


def test_order_cannot_be_created_without_items():
    with pytest.raises(EmptyOrderError):
        Order(customer_id="cust-1", items=[])


def test_order_item_rejects_non_positive_quantity():
    with pytest.raises(InvalidQuantityError):
        OrderItem(product_id="A", quantity=0, unit_price=Decimal("10.00"))


def test_order_item_rejects_negative_price():
    with pytest.raises(InvalidQuantityError):
        OrderItem(product_id="A", quantity=1, unit_price=Decimal("-1"))


def test_confirm_changes_status_to_confirmed():
    order = Order(
        customer_id="cust-1",
        items=[OrderItem(product_id="A", quantity=1, unit_price=Decimal("10"))],
    )

    order.confirm()

    assert order.status == OrderStatus.CONFIRMED


def test_cannot_confirm_a_cancelled_order():
    order = Order(
        customer_id="cust-1",
        items=[OrderItem(product_id="A", quantity=1, unit_price=Decimal("10"))],
    )
    order.cancel()

    with pytest.raises(ValueError):
        order.confirm()
