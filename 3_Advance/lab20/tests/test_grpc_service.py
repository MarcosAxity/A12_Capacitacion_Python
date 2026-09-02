"""Pruebas del OrdersServicer sin levantar un servidor gRPC real:
se instancia el servicer directamente y se usa un context de gRPC fake,
lo que hace las pruebas rápidas y deterministas (mismo espíritu que el
Módulo 10: aislar la unidad bajo prueba de infraestructura externa)."""
from __future__ import annotations

import grpc
import pytest

from generated import orders_pb2
from messaging.in_memory_publisher import InMemoryPublisher
from server.orders_servicer import OrdersServicer


class FakeContext:
    """Doble de prueba para grpc.ServicerContext: registra abort() en vez
    de lanzar una excepción real de gRPC, para poder inspeccionarla."""

    def __init__(self) -> None:
        self.aborted_with: tuple[grpc.StatusCode, str] | None = None

    def abort(self, code, details):
        self.aborted_with = (code, details)
        raise RuntimeError(details)  # simula el corte de ejecución real


@pytest.fixture
def publisher() -> InMemoryPublisher:
    return InMemoryPublisher()


@pytest.fixture
def servicer(publisher: InMemoryPublisher) -> OrdersServicer:
    return OrdersServicer(publisher=publisher)


def _sample_request() -> orders_pb2.CreateOrderRequest:
    return orders_pb2.CreateOrderRequest(
        customer_id="cliente-42",
        items=[
            orders_pb2.OrderItem(product_id="SKU-A", quantity=3, unit_price=10.0),
            orders_pb2.OrderItem(product_id="SKU-B", quantity=1, unit_price=25.5),
        ],
    )


def test_create_order_calcula_total_y_persiste(servicer: OrdersServicer):
    context = FakeContext()

    response = servicer.CreateOrder(_sample_request(), context)

    assert context.aborted_with is None
    assert response.order.order_id
    assert response.order.customer_id == "cliente-42"
    assert response.order.total_amount == pytest.approx(3 * 10.0 + 1 * 25.5)
    assert response.order.status == "CONFIRMED"


def test_create_order_publica_evento_order_created(servicer: OrdersServicer, publisher: InMemoryPublisher):
    context = FakeContext()
    response = servicer.CreateOrder(_sample_request(), context)

    assert len(publisher.published_events) == 1
    event = publisher.published_events[0]
    assert event.order_id == response.order.order_id
    assert event.customer_id == "cliente-42"
    assert event.total_amount == pytest.approx(response.order.total_amount)


def test_create_order_sin_items_rechaza(servicer: OrdersServicer):
    context = FakeContext()
    empty_request = orders_pb2.CreateOrderRequest(customer_id="cliente-42", items=[])

    with pytest.raises(RuntimeError):
        servicer.CreateOrder(empty_request, context)

    assert context.aborted_with is not None
    assert context.aborted_with[0] == grpc.StatusCode.INVALID_ARGUMENT


def test_get_order_encontrada(servicer: OrdersServicer):
    create_context = FakeContext()
    created = servicer.CreateOrder(_sample_request(), create_context).order

    get_context = FakeContext()
    response = servicer.GetOrder(orders_pb2.GetOrderRequest(order_id=created.order_id), get_context)

    assert get_context.aborted_with is None
    assert response.order.order_id == created.order_id


def test_get_order_no_encontrada(servicer: OrdersServicer):
    context = FakeContext()
    with pytest.raises(RuntimeError):
        servicer.GetOrder(orders_pb2.GetOrderRequest(order_id="no-existe"), context)

    assert context.aborted_with is not None
    assert context.aborted_with[0] == grpc.StatusCode.NOT_FOUND


def test_list_orders(servicer: OrdersServicer):
    servicer.CreateOrder(_sample_request(), FakeContext())
    servicer.CreateOrder(_sample_request(), FakeContext())

    response = servicer.ListOrders(orders_pb2.ListOrdersRequest(), FakeContext())

    assert len(response.orders) == 2
