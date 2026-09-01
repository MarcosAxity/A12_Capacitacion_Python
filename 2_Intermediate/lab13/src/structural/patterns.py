"""
Patrones estructurales
========================
Ejemplos de: Adapter, Facade, Composite, Decorator y Proxy.

El Adapter y el Decorator "completos" para el laboratorio viven en
src/lab/. Aqui se muestran versiones genericas para cubrir el contenido
teorico del modulo con otros casos de uso.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

# ---------------------------------------------------------------------------
# 1) ADAPTER (version generica, ver src/lab/external_provider_adapter.py
#    para el caso del laboratorio: proveedor externo de pagos)
# ---------------------------------------------------------------------------


class LectorDeAudioModerno(ABC):
    @abstractmethod
    def reproducir(self, archivo: str) -> str: ...


class ReproductorMP3Legado:
    """Clase 'externa' con una interfaz incompatible con la que espera
    nuestro sistema (simula una libreria de terceros que no controlamos)."""

    def play_mp3_file(self, ruta_archivo: str) -> str:
        return f"Reproduciendo MP3 (API legada): {ruta_archivo}"


class AdaptadorMP3(LectorDeAudioModerno):
    """Adapta la interfaz legada (play_mp3_file) a la interfaz moderna
    (reproducir) que espera el resto de la aplicacion."""

    def __init__(self, reproductor_legado: ReproductorMP3Legado):
        self._legado = reproductor_legado

    def reproducir(self, archivo: str) -> str:
        return self._legado.play_mp3_file(archivo)


# ---------------------------------------------------------------------------
# 2) FACADE
# ---------------------------------------------------------------------------
# Problema: dar una interfaz simple a un subsistema complejo (varios
# servicios que deben orquestarse para "procesar un pedido").


class ServicioInventario:
    def reservar_stock(self, sku: str, cantidad: int) -> bool:
        return True  # simulacion


class ServicioPagos:
    def cobrar(self, monto: float, tarjeta: str) -> str:
        return f"cobro-{tarjeta[-4:]}"


class ServicioEnvios:
    def crear_envio(self, direccion: str) -> str:
        return f"guia-{hash(direccion) % 10000}"


class FachadaPedidos:
    """Facade: oculta la complejidad de coordinar 3 subsistemas detras de
    un unico metodo simple para el cliente."""

    def __init__(self) -> None:
        self._inventario = ServicioInventario()
        self._pagos = ServicioPagos()
        self._envios = ServicioEnvios()

    def procesar_pedido(
        self, sku: str, cantidad: int, monto: float, tarjeta: str, direccion: str
    ) -> dict:
        if not self._inventario.reservar_stock(sku, cantidad):
            raise RuntimeError("Sin stock disponible")
        id_cobro = self._pagos.cobrar(monto, tarjeta)
        guia = self._envios.crear_envio(direccion)
        return {"cobro": id_cobro, "guia_envio": guia, "estado": "confirmado"}


# ---------------------------------------------------------------------------
# 3) COMPOSITE
# ---------------------------------------------------------------------------
# Problema: representar jerarquias parte-todo (carpetas y archivos, menus
# anidados, categorias de productos) tratando objetos individuales y
# composiciones de manera uniforme.


class ElementoSistemaArchivos(ABC):
    @abstractmethod
    def tamano_bytes(self) -> int: ...


class Archivo(ElementoSistemaArchivos):
    def __init__(self, nombre: str, tamano: int):
        self.nombre = nombre
        self._tamano = tamano

    def tamano_bytes(self) -> int:
        return self._tamano


class Carpeta(ElementoSistemaArchivos):
    def __init__(self, nombre: str):
        self.nombre = nombre
        self._hijos: list[ElementoSistemaArchivos] = []

    def agregar(self, elemento: ElementoSistemaArchivos) -> "Carpeta":
        self._hijos.append(elemento)
        return self

    def tamano_bytes(self) -> int:
        # El calculo es identico ya sea que el hijo sea un Archivo u otra
        # Carpeta: esa es la esencia del patron Composite.
        return sum(hijo.tamano_bytes() for hijo in self._hijos)


# ---------------------------------------------------------------------------
# 4) DECORATOR (version OOP clasica; ver src/lab/cache_decorator.py para
#    el decorator funcional de cache que pide el laboratorio)
# ---------------------------------------------------------------------------


class Bebida(ABC):
    @abstractmethod
    def costo(self) -> float: ...

    @abstractmethod
    def descripcion(self) -> str: ...


class Espresso(Bebida):
    def costo(self) -> float:
        return 1.80

    def descripcion(self) -> str:
        return "Espresso"


class DecoradorBebida(Bebida):
    """Decorator OOP: envuelve una Bebida y añade comportamiento sin
    modificar la clase original ni usar herencia rigida."""

    def __init__(self, bebida: Bebida):
        self._bebida = bebida


class ConLeche(DecoradorBebida):
    def costo(self) -> float:
        return self._bebida.costo() + 0.50

    def descripcion(self) -> str:
        return self._bebida.descripcion() + " + leche"


class ConCaramelo(DecoradorBebida):
    def costo(self) -> float:
        return self._bebida.costo() + 0.70

    def descripcion(self) -> str:
        return self._bebida.descripcion() + " + caramelo"


# ---------------------------------------------------------------------------
# 5) PROXY
# ---------------------------------------------------------------------------
# Problema: controlar el acceso a un objeto costoso o sensible (carga
# perezosa, control de permisos, logging) sin cambiar su interfaz.


class ServicioDatosSensibles(ABC):
    @abstractmethod
    def obtener(self, id_registro: str) -> str: ...


class ServicioDatosSensiblesReal(ServicioDatosSensibles):
    def obtener(self, id_registro: str) -> str:
        return f"datos-confidenciales-{id_registro}"


class ProxyControlAcceso(ServicioDatosSensibles):
    """Proxy de proteccion: verifica permisos antes de delegar al objeto
    real, sin que el cliente note la diferencia de interfaz."""

    def __init__(
        self, servicio_real: ServicioDatosSensiblesReal, es_admin: Callable[[], bool]
    ):
        self._servicio_real = servicio_real
        self._es_admin = es_admin

    def obtener(self, id_registro: str) -> str:
        if not self._es_admin():
            raise PermissionError("Acceso denegado: se requiere rol admin")
        return self._servicio_real.obtener(id_registro)
