"""Orders API - paquete distribuible como wheel.

Expone `create_app` (factory de FastAPI) y `__version__` para que el
wheel construido sea consumible tanto como librería como servicio.
"""

from typing import TYPE_CHECKING

from orders_api._version import __version__

if TYPE_CHECKING:
    from fastapi import FastAPI

__all__ = ["create_app", "__version__"]


def create_app() -> "FastAPI":  # import perezoso para evitar ciclos con orders_api.main
    from orders_api.main import create_app as _create_app

    return _create_app()
