"""Composition root: levanta el servidor gRPC en el puerto configurado.

Ejecución:
    python -m server.grpc_server
"""
from __future__ import annotations

import logging
import os
from concurrent import futures

import grpc

from generated import orders_pb2_grpc
from messaging.factory import get_publisher
from server.orders_servicer import OrdersServicer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def serve(port: int = 50051, block: bool = True) -> grpc.Server:
    publisher = get_publisher()  # backend elegido vía MESSAGING_BACKEND
    servicer = OrdersServicer(publisher=publisher)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    orders_pb2_grpc.add_OrdersServiceServicer_to_server(servicer, server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("Servidor gRPC OrdersService escuchando en el puerto %s", port)

    if block:
        try:
            server.wait_for_termination()
        except KeyboardInterrupt:
            server.stop(grace=1)
            publisher.close()
    return server


if __name__ == "__main__":
    serve(port=int(os.getenv("GRPC_PORT", "50051")))
