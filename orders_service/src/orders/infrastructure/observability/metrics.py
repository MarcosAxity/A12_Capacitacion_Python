"""Métricas Prometheus mínimas: contador de requests y histograma de latencia
por ruta/método/código, expuestas en /metrics.
"""
from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "orders_http_requests_total",
    "Total de requests HTTP recibidos",
    ["method", "path", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "orders_http_request_duration_seconds",
    "Latencia de requests HTTP en segundos",
    ["method", "path"],
)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
