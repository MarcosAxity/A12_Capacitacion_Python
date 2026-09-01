import pytest
from src.lab.pricing_strategy import (
    Carrito,
    ItemPrecio,
    PrecioClienteVIP,
    PrecioConCupon,
    PrecioOferta3x2,
    PrecioRegular,
)


@pytest.fixture
def items_ejemplo() -> list[ItemPrecio]:
    return [
        ItemPrecio(nombre="Camiseta", precio_unitario=200.0, cantidad=2),
        ItemPrecio(nombre="Gorra", precio_unitario=150.0, cantidad=1),
    ]


class TestPrecioRegular:
    def test_suma_simple_de_subtotales(self, items_ejemplo):
        carrito = Carrito(items=items_ejemplo)
        carrito.establecer_estrategia(PrecioRegular())
        assert carrito.total() == 550.0  # (200*2) + (150*1)

    def test_estrategia_por_defecto_es_regular(self, items_ejemplo):
        carrito = Carrito(items=items_ejemplo)
        assert carrito.estrategia_actual == "PrecioRegular"


class TestPrecioClienteVIP:
    def test_aplica_descuento_porcentual(self, items_ejemplo):
        carrito = Carrito(items=items_ejemplo)
        carrito.establecer_estrategia(PrecioClienteVIP(porcentaje_descuento=0.10))
        assert carrito.total() == pytest.approx(495.0)  # 550 * 0.9

    def test_rechaza_porcentaje_invalido(self):
        with pytest.raises(ValueError):
            PrecioClienteVIP(porcentaje_descuento=1.5)


class TestPrecioConCupon:
    def test_aplica_descuento_fijo(self, items_ejemplo):
        carrito = Carrito(items=items_ejemplo)
        carrito.establecer_estrategia(PrecioConCupon(monto_descuento=100.0))
        assert carrito.total() == 450.0

    def test_no_permite_total_negativo(self, items_ejemplo):
        carrito = Carrito(items=items_ejemplo)
        carrito.establecer_estrategia(PrecioConCupon(monto_descuento=99999.0))
        assert carrito.total() == 0.0

    def test_rechaza_descuento_negativo(self):
        with pytest.raises(ValueError):
            PrecioConCupon(monto_descuento=-10)


class TestPrecioOferta3x2:
    def test_paga_solo_dos_de_cada_tres(self):
        carrito = Carrito(
            items=[ItemPrecio(nombre="Playera", precio_unitario=100.0, cantidad=3)]
        )
        carrito.establecer_estrategia(PrecioOferta3x2())
        assert carrito.total() == 200.0

    def test_maneja_cantidades_no_multiplos_de_tres(self):
        carrito = Carrito(
            items=[ItemPrecio(nombre="Playera", precio_unitario=100.0, cantidad=7)]
        )
        carrito.establecer_estrategia(PrecioOferta3x2())
        # 7 = 2 grupos de 3 (pagan 2 c/u = 4 unidades) + 1 restante = 5 unidades pagadas
        assert carrito.total() == 500.0


class TestCambioDeEstrategiaEnCaliente:
    def test_se_puede_cambiar_estrategia_sin_recrear_el_carrito(self, items_ejemplo):
        carrito = Carrito(items=items_ejemplo)
        assert carrito.total() == 550.0

        carrito.establecer_estrategia(PrecioClienteVIP(0.20))
        assert carrito.total() == pytest.approx(440.0)
        assert carrito.estrategia_actual == "PrecioClienteVIP"
