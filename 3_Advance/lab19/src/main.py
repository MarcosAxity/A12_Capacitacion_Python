"""
main.py
=======

Aplicación FastAPI mínima que demuestra el uso de la configuración segura
(`Settings`) en un servicio real. Sirve como laboratorio ejecutable para
el Módulo 19.

Endpoints:
- GET /health   -> healthcheck (usado también por el HEALTHCHECK de Docker)
- GET /config   -> muestra la configuración activa con secretos enmascarados
- GET /whoami   -> demuestra el uso de un secreto (secret_key) sin exponerlo

Ejecutar localmente:
    uvicorn src.main:app --reload
"""

from __future__ import annotations

import hashlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import Settings, get_settings
from src.security_utils import redact_dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("modulo19")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    # Log seguro: se usa safe_dict(), jamás la config cruda.
    logger.info("Arrancando '%s' en modo %s", settings.app_name, settings.environment)
    logger.info("Config activa (secretos enmascarados): %s", redact_dict(settings.safe_dict()))
    yield


app = FastAPI(
    title="Módulo 19 - Seguridad y Mantenimiento",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict:
    """Usado por Docker HEALTHCHECK y por orquestadores (k8s liveness/readiness)."""
    return {"status": "ok"}


@app.get("/config")
def show_config(settings: Settings = None) -> dict:  # type: ignore[assignment]
    """Devuelve la configuración activa, con los campos secretos enmascarados.

    Nunca se debe exponer un endpoint que devuelva secretos en texto plano,
    ni siquiera en entornos de desarrollo.
    """
    settings = settings or get_settings()
    return redact_dict(settings.safe_dict())


@app.get("/whoami")
def whoami(settings: Settings = None) -> dict:  # type: ignore[assignment]
    """Ejemplo de uso legítimo de un secreto: se consume `secret_key` para
    derivar un hash determinista, pero el valor original nunca sale de la
    aplicación ni se refleja en la respuesta.
    """
    settings = settings or get_settings()
    fingerprint = hashlib.sha256(
        settings.secret_key.get_secret_value().encode("utf-8")
    ).hexdigest()[:12]
    return {"app": settings.app_name, "secret_fingerprint": fingerprint}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
