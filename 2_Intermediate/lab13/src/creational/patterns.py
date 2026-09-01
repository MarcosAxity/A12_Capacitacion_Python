"""
Patrones creacionales
======================
Ejemplos didacticos de: Factory Method, Abstract Factory, Builder y Singleton.

Cada ejemplo esta pensado para ser lo mas simple posible mientras conserva
la intencion real del patron (no son ejemplos "de juguete" desconectados
de un caso de uso practico).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# 1) FACTORY METHOD
# ---------------------------------------------------------------------------
# Problema: queremos crear distintos tipos de "notificaciones" (email, sms,
# push) sin que el codigo cliente conozca las clases concretas.


class Notificacion(ABC):
    @abstractmethod
    def enviar(self, mensaje: str) -> str: ...


class NotificacionEmail(Notificacion):
    def enviar(self, mensaje: str) -> str:
        return f"[EMAIL] {mensaje}"


class NotificacionSMS(Notificacion):
    def enviar(self, mensaje: str) -> str:
        return f"[SMS] {mensaje}"


class NotificacionPush(Notificacion):
    def enviar(self, mensaje: str) -> str:
        return f"[PUSH] {mensaje}"


class FabricaNotificaciones:
    """Factory Method: centraliza la logica de creacion."""

    _tipos = {
        "email": NotificacionEmail,
        "sms": NotificacionSMS,
        "push": NotificacionPush,
    }

    @classmethod
    def crear(cls, tipo: str) -> Notificacion:
        clase = cls._tipos.get(tipo)
        if clase is None:
            raise ValueError(f"Tipo de notificacion no soportado: {tipo}")
        return clase()


# ---------------------------------------------------------------------------
# 2) ABSTRACT FACTORY
# ---------------------------------------------------------------------------
# Problema: necesitamos crear "familias" de objetos relacionados que deben
# ser consistentes entre si (por ejemplo: componentes de UI para distintos
# "temas" visuales).


class Boton(ABC):
    @abstractmethod
    def renderizar(self) -> str: ...


class Checkbox(ABC):
    @abstractmethod
    def renderizar(self) -> str: ...


class BotonClaro(Boton):
    def renderizar(self) -> str:
        return "<boton estilo='claro'/>"


class CheckboxClaro(Checkbox):
    def renderizar(self) -> str:
        return "<checkbox estilo='claro'/>"


class BotonOscuro(Boton):
    def renderizar(self) -> str:
        return "<boton estilo='oscuro'/>"


class CheckboxOscuro(Checkbox):
    def renderizar(self) -> str:
        return "<checkbox estilo='oscuro'/>"


class FabricaUI(ABC):
    @abstractmethod
    def crear_boton(self) -> Boton: ...

    @abstractmethod
    def crear_checkbox(self) -> Checkbox: ...


class FabricaUIClara(FabricaUI):
    def crear_boton(self) -> Boton:
        return BotonClaro()

    def crear_checkbox(self) -> Checkbox:
        return CheckboxClaro()


class FabricaUIOscura(FabricaUI):
    def crear_boton(self) -> Boton:
        return BotonOscuro()

    def crear_checkbox(self) -> Checkbox:
        return CheckboxOscuro()


def construir_formulario(fabrica: FabricaUI) -> str:
    """El cliente solo depende de la interfaz FabricaUI, nunca de las
    clases concretas: puede cambiar de tema sin tocar esta funcion."""
    boton = fabrica.crear_boton()
    checkbox = fabrica.crear_checkbox()
    return boton.renderizar() + checkbox.renderizar()


# ---------------------------------------------------------------------------
# 3) BUILDER
# ---------------------------------------------------------------------------
# Problema: construir un objeto complejo (una consulta SQL, un reporte, una
# peticion HTTP) paso a paso, evitando constructores con 10 parametros.


@dataclass
class ConsultaSQL:
    tabla: str
    columnas: list[str] = field(default_factory=lambda: ["*"])
    condiciones: list[str] = field(default_factory=list)
    orden: Optional[str] = None
    limite: Optional[int] = None

    def to_sql(self) -> str:
        sql = f"SELECT {', '.join(self.columnas)} FROM {self.tabla}"
        if self.condiciones:
            sql += " WHERE " + " AND ".join(self.condiciones)
        if self.orden:
            sql += f" ORDER BY {self.orden}"
        if self.limite is not None:
            sql += f" LIMIT {self.limite}"
        return sql


class ConstructorConsultaSQL:
    """Builder fluido: cada metodo devuelve self para encadenar llamadas."""

    def __init__(self, tabla: str):
        self._tabla = tabla
        self._columnas: list[str] = ["*"]
        self._condiciones: list[str] = []
        self._orden: Optional[str] = None
        self._limite: Optional[int] = None

    def seleccionar(self, *columnas: str) -> "ConstructorConsultaSQL":
        self._columnas = list(columnas) or ["*"]
        return self

    def donde(self, condicion: str) -> "ConstructorConsultaSQL":
        self._condiciones.append(condicion)
        return self

    def ordenar_por(self, columna: str) -> "ConstructorConsultaSQL":
        self._orden = columna
        return self

    def limitar(self, n: int) -> "ConstructorConsultaSQL":
        self._limite = n
        return self

    def build(self) -> ConsultaSQL:
        return ConsultaSQL(
            tabla=self._tabla,
            columnas=self._columnas,
            condiciones=self._condiciones,
            orden=self._orden,
            limite=self._limite,
        )


# ---------------------------------------------------------------------------
# 4) SINGLETON (y cuando EVITARLO)
# ---------------------------------------------------------------------------
# Un Singleton clasico usando __new__. Uso legitimo: configuracion global de
# solo lectura cargada una vez, o un pool de conexiones costoso de crear.
#
# CUANDO EVITARLO (antipatron):
#   - Cuando se usa como "variable global disfrazada" para compartir estado
#     mutable entre modulos: dificulta testear (el estado persiste entre
#     tests) y crea acoplamiento oculto.
#   - Cuando el objeto tiene dependencias que en pruebas unitarias
#     necesitas mockear: un Singleton "duro" impide inyectar dobles de
#     prueba facilmente.
#   - En aplicaciones concurrentes/multihilo sin proteccion: puede crear
#     condiciones de carrera al inicializar la instancia.
#   - En codigo que podria correr en varios procesos/workers (p.ej. Gunicorn
#     con varios workers): cada proceso tendra su propio "singleton", lo que
#     rompe la suposicion de "instancia unica global".
#
# Alternativa recomendada en Python moderno: usar inyeccion de dependencias
# (pasar la instancia explicitamente) o un modulo (los modulos de Python ya
# son singletons por diseno del interprete).


class ConfiguracionApp:
    _instancia: Optional["ConfiguracionApp"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializado = False
        return cls._instancia

    def __init__(self, entorno: str = "produccion"):
        # Evita reinicializar en llamadas posteriores a ConfiguracionApp()
        if self._inicializado:
            return
        self.entorno = entorno
        self._inicializado = True

    @classmethod
    def reset_para_pruebas(cls) -> None:
        """Utilidad SOLO para tests: evita que el estado de un Singleton
        se filtre entre pruebas (una de las razones por las que este
        patron es incomodo de testear)."""
        cls._instancia = None
