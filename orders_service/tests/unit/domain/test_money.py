"""Pruebas unitarias del Value Object Money."""
from decimal import Decimal

import pytest

from orders.domain.value_objects import DomainValidationError, Money


@pytest.mark.unit
class TestMoney:
    def test_creates_with_valid_amount(self) -> None:
        money = Money(Decimal("100.50"), "MXN")
        assert money.amount == Decimal("100.50")
        assert money.currency == "MXN"

    def test_normalizes_currency_to_uppercase(self) -> None:
        money = Money(Decimal("10"), "mxn")
        assert money.currency == "MXN"

    def test_rounds_to_two_decimals(self) -> None:
        money = Money(Decimal("10.005"), "MXN")
        assert money.amount == Decimal("10.01")

    def test_rejects_negative_amount(self) -> None:
        with pytest.raises(DomainValidationError, match="negativo"):
            Money(Decimal("-1"), "MXN")

    def test_rejects_invalid_currency_code(self) -> None:
        with pytest.raises(DomainValidationError, match="ISO 4217"):
            Money(Decimal("1"), "MX")

    def test_addition_of_same_currency(self) -> None:
        result = Money(Decimal("10"), "MXN") + Money(Decimal("5"), "MXN")
        assert result == Money(Decimal("15"), "MXN")

    def test_addition_rejects_different_currency(self) -> None:
        with pytest.raises(DomainValidationError, match="distinta moneda"):
            Money(Decimal("10"), "MXN") + Money(Decimal("5"), "USD")

    def test_multiplication_by_positive_factor(self) -> None:
        result = Money(Decimal("10"), "MXN") * 3
        assert result == Money(Decimal("30"), "MXN")

    def test_multiplication_rejects_negative_factor(self) -> None:
        with pytest.raises(DomainValidationError, match="negativo"):
            Money(Decimal("10"), "MXN") * -1

    def test_zero_factory(self) -> None:
        assert Money.zero("USD") == Money(Decimal("0"), "USD")

    def test_is_immutable(self) -> None:
        money = Money(Decimal("10"), "MXN")
        with pytest.raises(AttributeError):
            money.amount = Decimal("20")  # type: ignore[misc]
