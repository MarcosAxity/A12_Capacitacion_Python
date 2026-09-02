"""Configuración del CLI mediante variables de entorno.

Todas las variables usan el prefijo ORDERS_ y pueden definirse en el
entorno del sistema o en un archivo .env en el directorio de trabajo:

    ORDERS_API_BASE_URL=http://127.0.0.1:8000
    ORDERS_API_TIMEOUT=5.0
    ORDERS_API_TOKEN=   (opcional, para APIs con auth Bearer)
"""
from __future__ import annotations

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ORDERS_", env_file=".env", extra="ignore")

    api_base_url: str = "http://127.0.0.1:8000"
    api_timeout: float = 5.0
    api_token: Optional[str] = None


def get_settings() -> Settings:
    """Punto único de acceso a la configuración (facilita el testing/mock)."""
    return Settings()
