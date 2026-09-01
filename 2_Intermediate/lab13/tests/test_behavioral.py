import pytest
from src.behavioral.patterns import (
    Catalogo,
    ComandoAgregarTexto,
    DocumentoTexto,
    HistorialComandos,
    NotificadorAlmacen,
    NotificadorCliente,
    OrdenarPorNombre,
    OrdenarPorPrecioAsc,
    Pedido,
    PedidoConEstado,
    ProcesadorCSV,
    ProcesadorJSON,
    SalaChat,
    UsuarioChat,
)


def test_strategy_ordena_por_precio():
    productos = [{"nombre": "B", "precio": 30}, {"nombre": "A", "precio": 10}]
    catalogo = Catalogo(OrdenarPorPrecioAsc())
    resultado = catalogo.listar(productos)
    assert [p["nombre"] for p in resultado] == ["A", "B"]


def test_strategy_cambia_algoritmo_en_runtime():
    productos = [{"nombre": "B", "precio": 30}, {"nombre": "A", "precio": 10}]
    catalogo = Catalogo(OrdenarPorPrecioAsc())
    catalogo.cambiar_estrategia(OrdenarPorNombre())
    resultado = catalogo.listar(productos)
    assert [p["nombre"] for p in resultado] == ["A", "B"]


def test_observer_notifica_a_todos_los_suscriptores():
    pedido = Pedido("p-1")
    cliente = NotificadorCliente()
    almacen = NotificadorAlmacen()
    pedido.suscribir(cliente)
    pedido.suscribir(almacen)

    pedido.cambiar_estado("confirmado")

    assert any("p-1" in m for m in cliente.mensajes)
    assert any("preparar pedido p-1" in m for m in almacen.mensajes)


def test_command_ejecutar_y_deshacer():
    doc = DocumentoTexto()
    historial = HistorialComandos()

    historial.ejecutar(ComandoAgregarTexto(doc, "Hola "))
    historial.ejecutar(ComandoAgregarTexto(doc, "Mundo"))
    assert doc.contenido == "Hola Mundo"

    historial.deshacer_ultimo()
    assert doc.contenido == "Hola "


def test_mediator_permite_comunicacion_indirecta():
    sala = SalaChat()
    ana = UsuarioChat("Ana", sala)
    luis = UsuarioChat("Luis", sala)

    ana.enviar_a("Luis", "Hola Luis")

    assert luis.bandeja_entrada == ["Ana: Hola Luis"]
    assert ana.bandeja_entrada == []


def test_template_method_mismo_esqueleto_distinto_paso():
    resultado_csv = ProcesadorCSV().procesar("datos.csv")
    resultado_json = ProcesadorJSON().procesar("datos.json")

    assert resultado_csv == "guardado:CONTENIDO-CRUDO-DE-DATOS.CSV"
    assert resultado_json == "guardado:{contenido-crudo-de-datos.json}"


def test_state_transiciones_validas():
    pedido = PedidoConEstado()
    assert pedido.nombre_estado == "EstadoCreado"

    pedido.confirmar()
    assert pedido.nombre_estado == "EstadoConfirmado"

    pedido.enviar()
    assert pedido.nombre_estado == "EstadoEnviado"


def test_state_transicion_invalida_lanza_error():
    pedido = PedidoConEstado()
    with pytest.raises(RuntimeError):
        pedido.enviar()  # no se puede enviar sin confirmar primero
