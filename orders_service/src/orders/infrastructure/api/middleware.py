"""Middlewares HTTP: correlación (request-id), logging estructurado y
métricas Prometheus por request.
"""
from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from orders.infrastructure.observability.metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = logging.getLogger("orders.http")

REQUEST_ID_HEADER = "X-Request-ID"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Asigna un request_id (o reusa el entrante), mide latencia, registra
    la petición en logs estructurados y actualiza métricas Prometheus.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration = time.perf_counter() - start
            logger.exception(
                "unhandled_exception",
                extra={"request_id": request_id, "path": request.url.path},
            )
            REQUEST_COUNT.labels(request.method, request.url.path, "500").inc()
            REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration)
            raise

        duration = time.perf_counter() - start
        response.headers[REQUEST_ID_HEADER] = request_id
        REQUEST_COUNT.labels(request.method, request.url.path, str(response.status_code)).inc()
        REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration)
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            },
        )
        return response
