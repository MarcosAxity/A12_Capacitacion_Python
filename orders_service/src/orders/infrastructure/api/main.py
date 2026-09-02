"""Punto de entrada de la API. Construye la app FastAPI, registra
middlewares, routers y el manejo de errores. Usa el patrón Application
Factory para poder crear instancias distintas en tests (con otra config).
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from orders.infrastructure.api.error_handlers import register_error_handlers
from orders.infrastructure.api.middleware import RequestContextMiddleware
from orders.infrastructure.api.routers import auth, health, orders
from orders.infrastructure.composition_root import AppContainer
from orders.infrastructure.config import Settings, get_settings
from orders.infrastructure.observability.logging_config import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.container = AppContainer.build(settings)
        yield
        await app.state.container.dispose()

    app = FastAPI(
        title="Orders Service",
        description=(
            "Servicio de órdenes construido con Arquitectura Hexagonal/Limpia "
            "(dominio, aplicación, infraestructura) — Proyecto final integrador."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)

    register_error_handlers(app)

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(orders.router)

    return app


app = create_app()
