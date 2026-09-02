"""Pruebas unitarias de la máquina de estados OrderStatus."""
import pytest

from orders.domain.value_objects import OrderStatus


@pytest.mark.unit
class TestOrderStatusTransitions:
    @pytest.mark.parametrize(
        "current,target,expected",
        [
            (OrderStatus.CREATED, OrderStatus.CONFIRMED, True),
            (OrderStatus.CREATED, OrderStatus.CANCELLED, True),
            (OrderStatus.CONFIRMED, OrderStatus.CANCELLED, True),
            (OrderStatus.CONFIRMED, OrderStatus.CREATED, False),
            (OrderStatus.CANCELLED, OrderStatus.CONFIRMED, False),
            (OrderStatus.CANCELLED, OrderStatus.CREATED, False),
        ],
    )
    def test_transition_matrix(
        self, current: OrderStatus, target: OrderStatus, expected: bool
    ) -> None:
        assert current.can_transition_to(target) is expected
