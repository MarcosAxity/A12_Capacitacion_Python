import pytest
from src.idiomatic.patterns import (
    ConexionBD,
    Dinero,
    ItemCarrito,
    medir_tiempo,
    reintentar,
    temporizador,
)


def test_decorador_medir_tiempo_expone_duracion():
    @medir_tiempo
    def sumar(a, b):
        return a + b

    assert sumar(2, 3) == 5
    assert sumar.ultima_duracion >= 0


def test_decorador_reintentar_reintenta_hasta_exito():
    intentos = {"n": 0}

    @reintentar(veces=3)
    def funcion_inestable():
        intentos["n"] += 1
        if intentos["n"] < 3:
            raise ValueError("fallo temporal")
        return "ok"

    assert funcion_inestable() == "ok"
    assert intentos["n"] == 3


def test_decorador_reintentar_agota_intentos_y_lanza_error():
    @reintentar(veces=2)
    def siempre_falla():
        raise ValueError("siempre falla")

    with pytest.raises(RuntimeError):
        siempre_falla()


def test_context_manager_cierra_conexion_incluso_con_excepcion():
    conexion = ConexionBD("dsn-de-prueba")
    with pytest.raises(ZeroDivisionError):
        with conexion:
            assert conexion.abierta is True
            1 / 0
    assert conexion.abierta is False


def test_context_manager_funcional_mide_duracion():
    with temporizador("prueba") as info:
        pass
    assert info["nombre"] == "prueba"
    assert info["duracion"] is not None and info["duracion"] >= 0


def test_dataclass_dinero_es_inmutable_y_comparable():
    a = Dinero(100.0, "MXN")
    b = Dinero(100.0, "MXN")
    assert a == b
    with pytest.raises(Exception):
        a.monto = 200.0  # frozen=True debe impedir la mutacion


def test_dataclass_dinero_suma_misma_moneda():
    total = Dinero(100.0).sumar(Dinero(50.0))
    assert total == Dinero(150.0)


def test_dataclass_dinero_rechaza_sumar_monedas_distintas():
    with pytest.raises(ValueError):
        Dinero(100.0, "MXN").sumar(Dinero(10.0, "USD"))


def test_dataclass_item_carrito_calcula_subtotal():
    item = ItemCarrito(sku="X1", nombre="Mouse", precio_unitario=250.0, cantidad=3)
    assert item.subtotal == 750.0
