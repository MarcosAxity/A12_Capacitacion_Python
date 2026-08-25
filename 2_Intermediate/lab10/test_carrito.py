from unittest.mock import Mock

import pytest
from carrito import Carrito, CuponInvalido
from hypothesis import given
from hypothesis import strategies as st


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------
@pytest.fixture
def carrito():
    c = Carrito()
    c.agregar(precio=100, cantidad=1)
    return c


# ---------------------------------------------------------------------
# Tests unitarios básicos (TDD - ciclo Red/Green)
# ---------------------------------------------------------------------
@pytest.mark.unit
def test_carrito_vacio_tiene_total_cero():
    assert Carrito().total() == 0


@pytest.mark.unit
def test_agregar_items_suma_al_total():
    c = Carrito()
    c.agregar(precio=10, cantidad=2)
    c.agregar(precio=5, cantidad=3)
    assert c.total() == 35


@pytest.mark.unit
def test_aplicar_descuento_valido_reduce_total(carrito):
    carrito.aplicar_cupon(porcentaje=20)
    assert carrito.total() == 80


# ---------------------------------------------------------------------
# Parametrización
# ---------------------------------------------------------------------
@pytest.mark.parametrize(
    "porcentaje, esperado",
    [
        (0, 100),
        (50, 50),
        (100, 0),
    ],
)
def test_aplicar_cupon_valores_limite(carrito, porcentaje, esperado):
    carrito.aplicar_cupon(porcentaje)
    assert carrito.total() == esperado


@pytest.mark.parametrize("porcentaje", [-10, -0.01, 101, 150])
def test_cupon_fuera_de_rango_lanza_error(carrito, porcentaje):
    with pytest.raises(CuponInvalido):
        carrito.aplicar_cupon(porcentaje)


# ---------------------------------------------------------------------
# Mocking con unittest.mock
# ---------------------------------------------------------------------
@pytest.mark.unit
def test_validador_externo_se_llama_con_el_porcentaje(carrito):
    validador = Mock(return_value=True)
    carrito.aplicar_cupon(20, validador_externo=validador)
    validador.assert_called_once_with(20)


@pytest.mark.unit
def test_si_validador_externo_rechaza_cupon_se_propaga_error(carrito):
    validador = Mock(side_effect=CuponInvalido("cupón vencido"))
    with pytest.raises(CuponInvalido):
        carrito.aplicar_cupon(20, validador_externo=validador)


# ---------------------------------------------------------------------
# Markers (ejemplo de prueba "lenta" que se puede excluir con -m "not slow")
# ---------------------------------------------------------------------
@pytest.mark.slow
def test_muchos_items_no_degrada_calculo():
    c = Carrito()
    for _ in range(10_000):
        c.agregar(precio=1, cantidad=1)
    assert c.total() == 10_000


# ---------------------------------------------------------------------
# Property-based testing con Hypothesis
# ---------------------------------------------------------------------
@given(
    precios=st.lists(
        st.floats(min_value=0, max_value=10_000, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=20,
    ),
    porcentaje=st.floats(
        min_value=0, max_value=100, allow_nan=False, allow_infinity=False
    ),
)
def test_total_con_descuento_siempre_entre_0_y_total_original(precios, porcentaje):
    c = Carrito()
    for p in precios:
        c.agregar(precio=p, cantidad=1)
    total_original = c.total()

    c.aplicar_cupon(porcentaje)

    assert 0 <= c.total() <= total_original


@given(
    porcentaje=st.floats(
        min_value=0, max_value=100, allow_nan=False, allow_infinity=False
    )
)
def test_cupon_valido_nunca_lanza_excepcion(porcentaje):
    # Propiedad: cualquier porcentaje dentro de [0, 100] es siempre aceptado.
    # Se crea el carrito dentro del test (no como fixture) porque Hypothesis
    # ejecuta muchas entradas por test y una fixture de function-scope no
    # se resetea entre esas ejecuciones.
    c = Carrito()
    c.agregar(precio=100, cantidad=1)
    c.aplicar_cupon(porcentaje)
