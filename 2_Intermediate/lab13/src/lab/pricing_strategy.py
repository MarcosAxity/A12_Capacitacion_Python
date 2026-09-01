"""
Laboratorio 1: Strategy para precios
=======================================
Caso de uso real: una tienda en linea necesita calcular el precio final de
un carrito segun distintas politicas comerciales (precio regular, cliente
VIP, cupon de descuento, oferta "3x2"), y esas politicas cambian con
frecuencia (campañas de marketing, temporadas, etc).

Sin Strategy, esto tipicamente termina en un metodo con un monton de
if/elif por "tipo de cliente" o "tipo de promocion" (antipatron: metodo
gigante dificil de extender sin romper lo existente -> viola el principio
Abierto/Cerrado).

Con Strategy:
  - Cada politica de precio es una clase independiente y testeable.
  - Agregar una politica nueva NO requiere modificar el codigo existente.
  - El contexto (Carrito) delega el calculo, sin conocer los detalles de
    cada estrategia.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ItemPrecio:
    nombre: str
    precio_unitario: float
    cantidad: int = 1

    @property
    def subtotal(self) -> float:
        return round(self.precio_unitario * self.cantidad, 2)


# ---------------------------------------------------------------------------
# Interfaz de la estrategia
# ---------------------------------------------------------------------------


class EstrategiaPrecio(ABC):
    """Interfaz comun para cualquier politica de calculo de precio."""

    @abstractmethod
    def calcular(self, items: list[ItemPrecio]) -> float:
        """Devuelve el precio final (ya con descuentos aplicados) para
        una lista de items."""
        ...

    @property
    def nombre(self) -> str:
        return type(self).__name__


# ---------------------------------------------------------------------------
# Estrategias concretas
# ---------------------------------------------------------------------------


class PrecioRegular(EstrategiaPrecio):
    """Sin ningun descuento: suma simple de subtotales."""

    def calcular(self, items: list[ItemPrecio]) -> float:
        return round(sum(item.subtotal for item in items), 2)


class PrecioClienteVIP(EstrategiaPrecio):
    """Descuento plano para clientes VIP."""

    def __init__(self, porcentaje_descuento: float = 0.10):
        if not 0 <= porcentaje_descuento <= 1:
            raise ValueError("El porcentaje debe estar entre 0 y 1")
        self._descuento = porcentaje_descuento

    def calcular(self, items: list[ItemPrecio]) -> float:
        base = sum(item.subtotal for item in items)
        return round(base * (1 - self._descuento), 2)


class PrecioConCupon(EstrategiaPrecio):
    """Descuento por un monto fijo, aplicado a traves de un codigo de
    cupon, con un piso de 0 (el total nunca puede quedar negativo)."""

    def __init__(self, monto_descuento: float):
        if monto_descuento < 0:
            raise ValueError("El descuento no puede ser negativo")
        self._monto_descuento = monto_descuento

    def calcular(self, items: list[ItemPrecio]) -> float:
        base = sum(item.subtotal for item in items)
        return round(max(base - self._monto_descuento, 0.0), 2)


class PrecioOferta3x2(EstrategiaPrecio):
    """Por cada 3 unidades del mismo producto, 1 sale gratis (se cobra el
    de menor precio dentro de cada grupo de 3, que es la version mas
    comun de esta promocion en retail)."""

    def calcular(self, items: list[ItemPrecio]) -> float:
        total = 0.0
        for item in items:
            grupos_de_tres, restantes = divmod(item.cantidad, 3)
            # En cada grupo de 3 se cobran 2 unidades.
            total += grupos_de_tres * 2 * item.precio_unitario
            total += restantes * item.precio_unitario
        return round(total, 2)


# ---------------------------------------------------------------------------
# Contexto
# ---------------------------------------------------------------------------


@dataclass
class Carrito:
    """Contexto del patron Strategy: mantiene una referencia a la
    estrategia activa y delega en ella el calculo del total."""

    items: list[ItemPrecio] = field(default_factory=list)
    _estrategia: EstrategiaPrecio = field(default_factory=PrecioRegular)

    def agregar_item(self, item: ItemPrecio) -> "Carrito":
        self.items.append(item)
        return self

    def establecer_estrategia(self, estrategia: EstrategiaPrecio) -> None:
        self._estrategia = estrategia

    def total(self) -> float:
        return self._estrategia.calcular(self.items)

    @property
    def estrategia_actual(self) -> str:
        return self._estrategia.nombre
