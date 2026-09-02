"""Prueba de integración end-to-end: levanta un servidor gRPC real en un
puerto efímero y lo consume con un stub real de gRPC, validando que el
contrato .proto generado funciona de punta a punta (no solo en memoria)."""
from __future__ import annotations

from concurrent import futures

import grpc
import pytest

from generated import orders_pb2, orders_pb2_grpc
from messaging.in_memory_publisher import InMemoryPublisher
from server.orders_servicer import OrdersServicer


@pytest.fixture
def grpc_server_address():
    publisher = InMemoryPublisher()
    servicer = OrdersServicer(publisher=publisher)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    orders_pb2_grpc.add_OrdersServiceServicer_to_server(servicer, server)
    port = server.add_insecure_port("[::]:0")  # puerto libre asignado por el SO
    server.start()

    yield f"localhost:{port}", publisher

    server.stop(grace=0)


def test_create_and_get_order_sobre_la_red(grpc_server_address):
    address, publisher = grpc_server_address

    with grpc.insecure_channel(address) as channel:
        stub = orders_pb2_grpc.OrdersServiceStub(channel)

        create_response = stub.CreateOrder(
            orders_pb2.CreateOrderRequest(
                customer_id="cliente-e2e",
                items=[orders_pb2.OrderItem(product_id="SKU-X", quantity=2, unit_price=50.0)],
            )
        )
        order_id = create_response.order.order_id
        assert create_response.order.total_amount == pytest.approx(100.0)

        get_response = stub.GetOrder(orders_pb2.GetOrderRequest(order_id=order_id))
        assert get_response.order.order_id == order_id

    assert len(publisher.published_events) == 1
