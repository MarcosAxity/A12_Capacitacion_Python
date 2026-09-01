"""Tests de las políticas de descuento (OCP).

Cada política se testea de forma AISLADA. Si mañana se agrega una
nueva política (por ejemplo `SeasonalDiscount`), basta con agregar un
nuevo test aquí abajo: no hace falta tocar ni las clases existentes ni
sus tests. Eso es "abierto a extensión, cerrado a modificación"
también reflejado en la suite de pruebas.
"""

import pytest
from src.domain.policies import (
    FixedAmountDiscount,
    NoDiscount,
    PercentageDiscount,
    ThresholdDiscount,
)


def test_no_discount_no_modifica_el_total():
    assert NoDiscount().apply(100.0) == 100.0


def test_percentage_discount_aplica_porcentaje():
    assert PercentageDiscount(0.25).apply(200.0) == 150.0


def test_percentage_discount_valida_rango():
    with pytest.raises(ValueError):
        PercentageDiscount(1.5)


def test_fixed_amount_discount_no_baja_de_cero():
    assert FixedAmountDiscount(amount=50).apply(30.0) == 0.0


def test_threshold_discount_aplica_solo_si_supera_umbral():
    policy = ThresholdDiscount(threshold=100.0, percentage=0.10)
    assert policy.apply(50.0) == 50.0  # no supera el umbral
    assert policy.apply(150.0) == 135.0  # supera el umbral
