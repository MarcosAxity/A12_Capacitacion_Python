"""
Patrones de comportamiento
============================
Ejemplos de: Strategy (version generica; la version completa del
laboratorio esta en src/lab/pricing_strategy.py), Observer, Command,
Mediator, Template Method y State.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

# ---------------------------------------------------------------------------
# 1) STRATEGY (version generica: algoritmos de ordenamiento de una lista
#    de productos). El caso de negocio completo -precios- esta en el lab.
# ---------------------------------------------------------------------------


class EstrategiaOrdenamiento(ABC):
    @abstractmethod
    def ordenar(self, productos: list[dict]) -> list[dict]: ...


class OrdenarPorPrecioAsc(EstrategiaOrdenamiento):
    def ordenar(self, productos: list[dict]) -> list[dict]:
        return sorted(productos, key=lambda p: p["precio"])


class OrdenarPorNombre(EstrategiaOrdenamiento):
    def ordenar(self, productos: list[dict]) -> list[dict]:
        return sorted(productos, key=lambda p: p["nombre"])


class Catalogo:
    def __init__(self, estrategia: EstrategiaOrdenamiento):
        self._estrategia = estrategia

    def cambiar_estrategia(self, estrategia: EstrategiaOrdenamiento) -> None:
        self._estrategia = estrategia

    def listar(self, productos: list[dict]) -> list[dict]:
        return self._estrategia.ordenar(productos)


# ---------------------------------------------------------------------------
# 2) OBSERVER
# ---------------------------------------------------------------------------
# Problema: notificar a multiples "suscriptores" cuando cambia el estado de
# un objeto (patron pub/sub clasico), sin acoplar al "publisher" con
# implementaciones concretas de los suscriptores.


class ObservadorPedido(ABC):
    @abstractmethod
    def actualizar(self, pedido_id: str, nuevo_estado: str) -> None: ...


class NotificadorCliente(ObservadorPedido):
    def __init__(self):
        self.mensajes: list[str] = []

    def actualizar(self, pedido_id: str, nuevo_estado: str) -> None:
        self.mensajes.append(
            f"Cliente notificado: pedido {pedido_id} -> {nuevo_estado}"
        )


class NotificadorAlmacen(ObservadorPedido):
    def __init__(self):
        self.mensajes: list[str] = []

    def actualizar(self, pedido_id: str, nuevo_estado: str) -> None:
        if nuevo_estado == "confirmado":
            self.mensajes.append(f"Almacen: preparar pedido {pedido_id}")


class Pedido:
    """Sujeto observable: mantiene una lista de observadores y los notifica
    ante cambios de estado."""

    def __init__(self, pedido_id: str):
        self.pedido_id = pedido_id
        self._estado = "creado"
        self._observadores: list[ObservadorPedido] = []

    def suscribir(self, observador: ObservadorPedido) -> None:
        self._observadores.append(observador)

    def cambiar_estado(self, nuevo_estado: str) -> None:
        self._estado = nuevo_estado
        for obs in self._observadores:
            obs.actualizar(self.pedido_id, nuevo_estado)


# ---------------------------------------------------------------------------
# 3) COMMAND
# ---------------------------------------------------------------------------
# Problema: encapsular una accion (y sus datos) como un objeto, para poder
# encolarla, deshacerla (undo) o registrarla en un historial.


class Comando(ABC):
    @abstractmethod
    def ejecutar(self) -> None: ...

    @abstractmethod
    def deshacer(self) -> None: ...


class DocumentoTexto:
    def __init__(self):
        self.contenido = ""

    def agregar_texto(self, texto: str) -> None:
        self.contenido += texto

    def quitar_ultimos(self, n: int) -> None:
        self.contenido = self.contenido[:-n] if n else self.contenido


class ComandoAgregarTexto(Comando):
    def __init__(self, documento: DocumentoTexto, texto: str):
        self._documento = documento
        self._texto = texto

    def ejecutar(self) -> None:
        self._documento.agregar_texto(self._texto)

    def deshacer(self) -> None:
        self._documento.quitar_ultimos(len(self._texto))


class HistorialComandos:
    """Invoker: ejecuta comandos y permite deshacerlos (undo)."""

    def __init__(self):
        self._pila: list[Comando] = []

    def ejecutar(self, comando: Comando) -> None:
        comando.ejecutar()
        self._pila.append(comando)

    def deshacer_ultimo(self) -> None:
        if self._pila:
            self._pila.pop().deshacer()


# ---------------------------------------------------------------------------
# 4) MEDIATOR
# ---------------------------------------------------------------------------
# Problema: evitar que N componentes se comuniquen directamente entre si
# (acoplamiento N x N); en su lugar, todos hablan con un mediador central.


class SalaChat:
    """Mediator: centraliza la comunicacion entre usuarios."""

    def __init__(self):
        self._usuarios: dict[str, "UsuarioChat"] = {}

    def registrar(self, usuario: "UsuarioChat") -> None:
        self._usuarios[usuario.nombre] = usuario

    def enviar(self, remitente: str, destinatario: str, mensaje: str) -> None:
        usuario_destino = self._usuarios.get(destinatario)
        if usuario_destino:
            usuario_destino.recibir(remitente, mensaje)


class UsuarioChat:
    def __init__(self, nombre: str, sala: SalaChat):
        self.nombre = nombre
        self._sala = sala
        self.bandeja_entrada: list[str] = []
        sala.registrar(self)

    def enviar_a(self, destinatario: str, mensaje: str) -> None:
        self._sala.enviar(self.nombre, destinatario, mensaje)

    def recibir(self, remitente: str, mensaje: str) -> None:
        self.bandeja_entrada.append(f"{remitente}: {mensaje}")


# ---------------------------------------------------------------------------
# 5) TEMPLATE METHOD
# ---------------------------------------------------------------------------
# Problema: definir el "esqueleto" de un algoritmo en la clase base y dejar
# que las subclases sobrescriban solo ciertos pasos, sin duplicar la
# estructura general.


class ProcesadorArchivo(ABC):
    def procesar(self, ruta: str) -> str:
        """Template method: define el orden fijo de pasos."""
        datos = self._leer(ruta)
        datos_transformados = self._transformar(datos)
        return self._guardar(datos_transformados)

    def _leer(self, ruta: str) -> str:
        return f"contenido-crudo-de-{ruta}"

    @abstractmethod
    def _transformar(self, datos: str) -> str: ...

    def _guardar(self, datos: str) -> str:
        return f"guardado:{datos}"


class ProcesadorCSV(ProcesadorArchivo):
    def _transformar(self, datos: str) -> str:
        return datos.upper()


class ProcesadorJSON(ProcesadorArchivo):
    def _transformar(self, datos: str) -> str:
        return "{" + datos + "}"


# ---------------------------------------------------------------------------
# 6) STATE
# ---------------------------------------------------------------------------
# Problema: el comportamiento de un objeto depende de su estado interno
# (una maquina de estados), evitando condicionales gigantes tipo
# if/elif encadenados por todo el codigo.


class EstadoPedido(ABC):
    @abstractmethod
    def confirmar(self, pedido: "PedidoConEstado") -> None: ...

    @abstractmethod
    def enviar(self, pedido: "PedidoConEstado") -> None: ...

    @abstractmethod
    def cancelar(self, pedido: "PedidoConEstado") -> None: ...


class EstadoCreado(EstadoPedido):
    def confirmar(self, pedido: "PedidoConEstado") -> None:
        pedido.estado = EstadoConfirmado()

    def enviar(self, pedido: "PedidoConEstado") -> None:
        raise RuntimeError("No se puede enviar un pedido sin confirmar")

    def cancelar(self, pedido: "PedidoConEstado") -> None:
        pedido.estado = EstadoCancelado()


class EstadoConfirmado(EstadoPedido):
    def confirmar(self, pedido: "PedidoConEstado") -> None:
        raise RuntimeError("El pedido ya esta confirmado")

    def enviar(self, pedido: "PedidoConEstado") -> None:
        pedido.estado = EstadoEnviado()

    def cancelar(self, pedido: "PedidoConEstado") -> None:
        pedido.estado = EstadoCancelado()


class EstadoEnviado(EstadoPedido):
    def confirmar(self, pedido: "PedidoConEstado") -> None:
        raise RuntimeError("El pedido ya fue enviado")

    def enviar(self, pedido: "PedidoConEstado") -> None:
        raise RuntimeError("El pedido ya fue enviado")

    def cancelar(self, pedido: "PedidoConEstado") -> None:
        raise RuntimeError("No se puede cancelar un pedido ya enviado")


class EstadoCancelado(EstadoPedido):
    def confirmar(self, pedido: "PedidoConEstado") -> None:
        raise RuntimeError("El pedido esta cancelado")

    def enviar(self, pedido: "PedidoConEstado") -> None:
        raise RuntimeError("El pedido esta cancelado")

    def cancelar(self, pedido: "PedidoConEstado") -> None:
        raise RuntimeError("El pedido ya esta cancelado")


class PedidoConEstado:
    """Context: delega el comportamiento en el objeto EstadoPedido actual."""

    def __init__(self):
        self.estado: EstadoPedido = EstadoCreado()

    def confirmar(self) -> None:
        self.estado.confirmar(self)

    def enviar(self) -> None:
        self.estado.enviar(self)

    def cancelar(self) -> None:
        self.estado.cancelar(self)

    @property
    def nombre_estado(self) -> str:
        return type(self.estado).__name__
