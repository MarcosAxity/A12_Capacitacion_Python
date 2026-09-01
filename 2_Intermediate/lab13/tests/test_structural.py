import pytest
from src.structural.patterns import (
    AdaptadorMP3,
    Archivo,
    Carpeta,
    ConCaramelo,
    ConLeche,
    Espresso,
    FachadaPedidos,
    ProxyControlAcceso,
    ReproductorMP3Legado,
    ServicioDatosSensiblesReal,
)


def test_adapter_traduce_interfaz_legada():
    adaptador = AdaptadorMP3(ReproductorMP3Legado())
    assert "cancion.mp3" in adaptador.reproducir("cancion.mp3")


def test_facade_orquesta_subsistemas():
    fachada = FachadaPedidos()
    resultado = fachada.procesar_pedido(
        sku="ABC123",
        cantidad=1,
        monto=299.0,
        tarjeta="4111111111111111",
        direccion="Calle 1",
    )
    assert resultado["estado"] == "confirmado"
    assert "cobro" in resultado and "guia_envio" in resultado


def test_composite_suma_tamanos_recursivamente():
    raiz = Carpeta("raiz")
    sub = Carpeta("sub")
    sub.agregar(Archivo("a.txt", 100)).agregar(Archivo("b.txt", 50))
    raiz.agregar(sub).agregar(Archivo("c.txt", 25))

    assert raiz.tamano_bytes() == 175


def test_decorator_oop_compone_costos_y_descripcion():
    bebida = ConCaramelo(ConLeche(Espresso()))
    assert bebida.costo() == pytest.approx(1.80 + 0.50 + 0.70)
    assert bebida.descripcion() == "Espresso + leche + caramelo"


def test_proxy_bloquea_acceso_sin_permisos():
    proxy = ProxyControlAcceso(ServicioDatosSensiblesReal(), es_admin=lambda: False)
    with pytest.raises(PermissionError):
        proxy.obtener("registro-1")


def test_proxy_permite_acceso_con_permisos():
    proxy = ProxyControlAcceso(ServicioDatosSensiblesReal(), es_admin=lambda: True)
    assert proxy.obtener("registro-1") == "datos-confidenciales-registro-1"
