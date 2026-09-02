"""Pruebas basadas en propiedades (Hypothesis) para invariantes del dominio
que deben cumplirse para *cualquier* entrada válida, no solo casos puntuales.
"""
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from orders.domain.entities import Order
from orders.domain.value_objects import Money, ProductRef

money_amounts = st.decimals(
    min_value=Decimal("0.01"),
    max_value=Decimal("10000"),
    places=2,
    allow_nan=False,
    allow_infinity=False,
)
quantities = st.integers(min_value=1, max_value=100)


@pytest.mark.unit
class TestMoneyProperties:
    @given(a=money_amounts, b=money_amounts)
    def test_addition_is_commutative(self, a: Decimal, b: Decimal) -> None:
        assert Money(a) + Money(b) == Money(b) + Money(a)

    @given(amount=money_amounts, factor=st.integers(min_value=0, max_value=1000))
    def test_multiplication_never_produces_negative(self, amount: Decimal, factor: int) -> None:
        result = Money(amount) * factor
        assert result.amount >= 0

    @given(amount=money_amounts)
    def test_amount_always_has_at_most_two_decimals(self, amount: Decimal) -> None:
        money = Money(amount)
        assert money.amount == money.amount.quantize(Decimal("0.01"))


@pytest.mark.unit
class TestOrderTotalProperties:
    @given(
        quantities_and_prices=st.lists(
            st.tuples(quantities, money_amounts), min_size=0, max_size=20
        )
    )
    def test_total_is_never_negative_and_matches_sum_of_subtotals(
        self, quantities_and_prices: list[tuple[int, Decimal]]
    ) -> None:
        order = Order.create(customer_id="cust-1")
        expected = Decimal("0.00")
        for i, (qty, price) in enumerate(quantities_and_prices):
            order.add_item(ProductRef(f"prod-{i}", f"Producto {i}"), qty, price)
            expected += (Money(price).amount * qty)

        assert order.total().amount >= 0
        assert order.total().amount == expected.quantize(Decimal("0.01"))
