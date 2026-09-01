"""
Laboratorio 2: Decorator de cache
====================================
Caso de uso real: una funcion que consulta un servicio externo (o hace un
calculo costoso) se llama repetidamente con los mismos argumentos. En vez
de repetir el trabajo/costo cada vez, un decorator de cache guarda el
resultado y lo reutiliza durante un tiempo de vida (TTL) configurable.

Este es el patron Decorator en su forma "idiomatica" de Python: en lugar
de una jerarquia de clases que envuelven un objeto, usamos una funcion
que envuelve a otra funcion (mismo principio: añadir comportamiento sin
modificar el codigo original ni usar herencia).

Incluye:
  - `cache_con_ttl`: decorator generico configurable (tamaño maximo y TTL).
  - Metricas de aciertos/fallos (hits/misses) accesibles para pruebas y
    monitoreo, replicando lo que ofreceria una libreria real de cache.
"""

from __future__ import annotations

import functools
import time
from dataclasses import dataclass
from typing import Any, Callable, Hashable


@dataclass
class _EntradaCache:
    valor: Any
    expira_en: float


@dataclass
class EstadisticasCache:
    hits: int = 0
    misses: int = 0

    @property
    def total_llamadas(self) -> int:
        return self.hits + self.misses

    @property
    def tasa_aciertos(self) -> float:
        if self.total_llamadas == 0:
            return 0.0
        return round(self.hits / self.total_llamadas, 4)


def _clave_para(args: tuple, kwargs: dict) -> Hashable:
    """Genera una clave hashable a partir de los argumentos. Si algun
    argumento no es hashable, se usa su repr como fallback (suficiente
    para el proposito didactico de este laboratorio)."""
    try:
        return (args, tuple(sorted(kwargs.items())))
    except TypeError:
        return repr((args, kwargs))


def cache_con_ttl(
    ttl_segundos: float = 60.0,
    tamano_maximo: int = 128,
    reloj: Callable[[], float] = time.monotonic,
) -> Callable:
    """Decorator factory: crea un decorator de cache con:
    - `ttl_segundos`: cuanto tiempo se considera valido un resultado
      cacheado antes de recalcularlo.
    - `tamano_maximo`: limite de entradas (politica simple FIFO al
      superarlo, para no crecer sin control -> evita el antipatron de
      "cache sin limite" que provoca fugas de memoria).
    - `reloj`: inyectable para poder testear el TTL sin usar time.sleep
      real (facilita pruebas deterministas con pytest).
    """

    def decorador(func: Callable) -> Callable:
        almacen: dict[Hashable, _EntradaCache] = {}
        orden_insercion: list[Hashable] = []
        stats = EstadisticasCache()

        @functools.wraps(func)
        def envoltorio(*args: Any, **kwargs: Any) -> Any:
            clave = _clave_para(args, kwargs)
            ahora = reloj()

            entrada = almacen.get(clave)
            if entrada is not None and entrada.expira_en > ahora:
                stats.hits += 1
                return entrada.valor

            # Cache miss (no existe o expiro): recalculamos.
            stats.misses += 1
            resultado = func(*args, **kwargs)

            if clave not in almacen and len(almacen) >= tamano_maximo:
                # Politica de desalojo FIFO simple.
                clave_mas_antigua = orden_insercion.pop(0)
                almacen.pop(clave_mas_antigua, None)

            if clave not in almacen:
                orden_insercion.append(clave)

            almacen[clave] = _EntradaCache(
                valor=resultado, expira_en=ahora + ttl_segundos
            )
            return resultado

        def invalidar(*args: Any, **kwargs: Any) -> None:
            """Permite invalidar manualmente una entrada especifica."""
            clave = _clave_para(args, kwargs)
            almacen.pop(clave, None)
            if clave in orden_insercion:
                orden_insercion.remove(clave)

        def limpiar_cache() -> None:
            almacen.clear()
            orden_insercion.clear()

        # Se exponen utilidades/metricas como atributos de la funcion
        # decorada, un patron muy comun en Python (ej. lru_cache.cache_info).
        envoltorio.cache_info = lambda: stats  # type: ignore[attr-defined]
        envoltorio.invalidar = invalidar  # type: ignore[attr-defined]
        envoltorio.limpiar_cache = limpiar_cache  # type: ignore[attr-defined]
        envoltorio.tamano_actual = lambda: len(almacen)  # type: ignore[attr-defined]

        return envoltorio

    return decorador
