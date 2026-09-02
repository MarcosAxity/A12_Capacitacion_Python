"""Endpoints de observabilidad: liveness/readiness y métricas Prometheus."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from orders.infrastructure.api.schemas import HealthResponse
from orders.infrastructure.config import Settings, get_settings
from orders.infrastructure.observability.metrics import render_metrics

router = APIRouter(tags=["observability"])


@router.get("/health", response_model=HealthResponse)
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    """Liveness/readiness probe usado por Docker y orquestadores."""
    return HealthResponse(status="ok", environment=settings.environment)


@router.get("/metrics")
async def metrics() -> Response:
    """Expone métricas en formato Prometheus (contadores de requests, latencia)."""
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)
