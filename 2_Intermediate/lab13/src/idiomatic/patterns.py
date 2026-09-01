"""
Patrones idiomaticos de Python
=================================
Python ofrece mecanismos nativos que resuelven, de forma mas ligera y
"pythonica", problemas que en otros lenguajes se resuelven con los GoF
patterns clasicos:

  - Decoradores de funcion  -> version funcional del patron Decorator.
  - Context managers (with) -> version idiomatica del patron RAII /
                                similar a un "Proxy" para adquirir y
                                liberar recursos de forma segura.
  - Dataclasses              -> alternativa ligera al patron Builder /
                                Value Object para clases centradas en datos.
"""

from __future__ import annotations

import functools
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator

# ---------------------------------------------------------------------------
# 1) DECORADORES DE FUNCION
# ---------------------------------------------------------------------------


def medir_tiempo(func: Callable) -> Callable:
    """Decorador simple que mide cuanto tarda una funcion en ejecutarse."""

    @functools.wraps(func)
    def envoltorio(*args: Any, **kwargs: Any) -> Any:
        inicio = time.perf_counter()
        resultado = func(*args, **kwargs)
        duracion = time.perf_counter() - inicio
        envoltorio.ultima_duracion = duracion  # type: ignore[attr-defined]
        return resultado

    envoltorio.ultima_duracion = 0.0  # type: ignore[attr-defined]
    return envoltorio


def reintentar(veces: int = 3):
    """Decorador parametrizable ('decorator factory'): reintenta una
    funcion hasta `veces` veces si lanza una excepcion."""

    def decorador(func: Callable) -> Callable:
        @functools.wraps(func)
        def envoltorio(*args: Any, **kwargs: Any) -> Any:
            ultimo_error: Exception | None = None
            for intento in range(1, veces + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as err:  # noqa: BLE001 - ejemplo didactico
                    ultimo_error = err
            raise RuntimeError(
                f"Fallo tras {veces} intentos: {ultimo_error}"
            ) from ultimo_error

        return envoltorio

    return decorador


# ---------------------------------------------------------------------------
# 2) CONTEXT MANAGERS
# ---------------------------------------------------------------------------


class ConexionBD:
    """Simula una conexion a base de datos que debe abrirse y cerrarse
    de forma segura, incluso si ocurre una excepcion dentro del bloque."""

    def __init__(self, dsn: str):
        self.dsn = dsn
        self.abierta = False

    def __enter__(self) -> "ConexionBD":
        self.abierta = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.abierta = False
        # Al devolver False (o None), cualquier excepcion se sigue
        # propagando normalmente; no la "tragamos" en silencio.
        return False

    def ejecutar(self, query: str) -> str:
        if not self.abierta:
            raise RuntimeError("La conexion no esta abierta")
        return f"resultado({query})"


@contextmanager
def temporizador(nombre: str) -> Iterator[dict]:
    """Version funcional de un context manager usando @contextmanager,
    alternativa mas concisa a implementar __enter__/__exit__."""
    info: dict = {"nombre": nombre, "duracion": None}
    inicio = time.perf_counter()
    try:
        yield info
    finally:
        info["duracion"] = time.perf_counter() - inicio


# ---------------------------------------------------------------------------
# 3) DATACLASSES
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Dinero:
    """Value Object inmutable: dos instancias con los mismos valores son
    iguales entre si (__eq__ generado automaticamente) y no se pueden
    mutar accidentalmente (frozen=True)."""

    monto: float
    moneda: str = "MXN"

    def sumar(self, otro: "Dinero") -> "Dinero":
        if self.moneda != otro.moneda:
            raise ValueError("No se pueden sumar montos en distinta moneda")
        return Dinero(self.monto + otro.monto, self.moneda)


@dataclass
class ItemCarrito:
    sku: str
    nombre: str
    precio_unitario: float
    cantidad: int = 1
    etiquetas: list[str] = field(default_factory=list)

    @property
    def subtotal(self) -> float:
        return round(self.precio_unitario * self.cantidad, 2)
