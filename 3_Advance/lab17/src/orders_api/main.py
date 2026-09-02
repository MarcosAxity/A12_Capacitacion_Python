"""Factory de la aplicación FastAPI y punto de entrada del servicio."""

from __future__ import annotations

from fastapi import FastAPI

from orders_api._version import __version__ as _version
from orders_api.models import HealthResponse
from orders_api.routes import router as orders_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Orders API",
        version=_version,
        description="Servicio de referencia para el Módulo 17 (empaquetado, Docker y CI/CD).",
    )
    app.include_router(orders_router)

    @app.get("/health", response_model=HealthResponse, tags=["infra"])
    def health() -> HealthResponse:
        return HealthResponse(version=_version)

    return app


app = create_app()


def run() -> None:  # entry point registrado en pyproject.toml -> orders-api
    import uvicorn

    uvicorn.run("orders_api.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    run()
