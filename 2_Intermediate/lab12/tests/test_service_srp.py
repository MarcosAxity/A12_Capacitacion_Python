"""Tests de `OrderService` usando un repositorio y un notifier FALSOS,
escritos a mano (sin base de datos, sin red, sin librerías de mocking).

Esto es posible gracias a DIP: como `OrderService` solo depende de los
Protocols `OrderRepository` y `Notifier`, cualquier objeto que tenga
los métodos correctos sirve como test double. Esto demuestra que
aplicar SOLID mejora directamente la TESTABILIDAD.
"""

import pytest
from src.domain.models import OrderStatus
from src.domain.policies import PercentageDiscount
from src.domain.services import OrderNotFoundError, OrderService
from src.infrastructure.memory_repository import InMemoryOrderRepository
from src.infrastructure.notifiers import ConsoleNotifier


@pytest.fixture
def service() -> OrderService:
    # Se usa la implementación en memoria como "fake" liviano: no hay
    # necesidad de una librería de mocks porque el contrato es chico
    # (ISP) y la implementación es trivial.
    return OrderService(
        repository=InMemoryOrderRepository(),
        notifier=ConsoleNotifier(),
        discount_policy=PercentageDiscount(percentage=0.20),
    )


def test_place_order_crea_pedido_en_estado_created(service: OrderService):
    order = service.place_order(customer="ana@example.com", total=100.0)

    assert order.status == OrderStatus.CREATED
    assert order.total == 100.0
    assert service.list_orders() == [order]


def test_apply_discount_usa_la_politica_inyectada(service: OrderService):
    order = service.place_order(customer="ana@example.com", total=100.0)

    updated = service.apply_discount(order.id)

    assert updated.total == 80.0  # 20% de descuento
    assert updated.status == OrderStatus.DISCOUNTED


def test_notify_customer_envia_mensaje_y_actualiza_estado(service: OrderService):
    order = service.place_order(customer="ana@example.com", total=100.0)

    service.notify_customer(order.id, message="hola")

    notifier: ConsoleNotifier = service._notifier  # type: ignore[attr-defined]
    assert ("ana@example.com", "hola") in notifier.sent
    assert service._repository.get(order.id).status == OrderStatus.NOTIFIED  # type: ignore[union-attr]


def test_operar_sobre_pedido_inexistente_lanza_error_de_dominio(service: OrderService):
    with pytest.raises(OrderNotFoundError):
        service.apply_discount("id-inexistente")
