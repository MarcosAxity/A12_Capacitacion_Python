"""Cliente gRPC de demostración para OrdersService.

Ejecución (con el servidor ya corriendo):
    python -m client.grpc_client
"""
from __future__ import annotations

import os

import grpc

from generated import orders_pb2, orders_pb2_grpc


def run(target: str = "localhost:50051") -> None:
    with grpc.insecure_channel(target) as channel:
        stub = orders_pb2_grpc.OrdersServiceStub(channel)

        request = orders_pb2.CreateOrderRequest(
            customer_id="cliente-001",
            items=[
                orders_pb2.OrderItem(product_id="SKU-1", quantity=2, unit_price=150.0),
                orders_pb2.OrderItem(product_id="SKU-2", quantity=1, unit_price=99.9),
            ],
        )
        create_response = stub.CreateOrder(request)
        order = create_response.order
        print(f"Orden creada -> id={order.order_id} total={order.total_amount:.2f} status={order.status}")

        get_response = stub.GetOrder(orders_pb2.GetOrderRequest(order_id=order.order_id))
        print(f"Orden consultada -> {get_response.order}")

        list_response = stub.ListOrders(orders_pb2.ListOrdersRequest())
        print(f"Total de órdenes en el servidor: {len(list_response.orders)}")


if __name__ == "__main__":
    run(target=os.getenv("GRPC_TARGET", "localhost:50051"))
