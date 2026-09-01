import pytest
from src.lab.external_provider_adapter import (
    AdaptadorProveedorExterno,
    ProveedorPagoExternoSDK,
)


@pytest.fixture
def sdk_externo() -> ProveedorPagoExternoSDK:
    return ProveedorPagoExternoSDK(api_key="clave-de-prueba")


@pytest.fixture
def pasarela(sdk_externo) -> AdaptadorProveedorExterno:
    return AdaptadorProveedorExterno(sdk_externo)


class TestCobro:
    def test_cobro_exitoso_traduce_centavos_a_formato_del_proveedor(self, pasarela):
        resultado = pasarela.cobrar(
            monto_centavos=15000, moneda="mxn", referencia="pedido-1"
        )

        assert resultado.exitoso is True
        assert resultado.id_transaccion.startswith("ext-charge-")

    def test_moneda_se_normaliza_a_mayusculas(self, pasarela, sdk_externo):
        pasarela.cobrar(monto_centavos=1000, moneda="usd", referencia="pedido-2")
        # Verificamos indirectamente a traves del estado interno del SDK
        # simulado, para confirmar que el Adapter tradujo bien el dato.
        (transaccion,) = sdk_externo._transacciones.values()
        assert transaccion["currency"] == "USD"

    def test_rechaza_montos_no_positivos_sin_llamar_al_sdk(self, pasarela, sdk_externo):
        resultado = pasarela.cobrar(
            monto_centavos=0, moneda="mxn", referencia="pedido-3"
        )

        assert resultado.exitoso is False
        assert sdk_externo._transacciones == {}

    def test_traduce_error_del_proveedor_a_resultado_propio(
        self, pasarela, sdk_externo, monkeypatch
    ):
        # Simulamos que el SDK externo devuelve un error inesperado.
        def create_charge_con_error(*args, **kwargs):
            return {"ok": False, "error_code": "PROVIDER_DOWN", "charge_id": None}

        monkeypatch.setattr(sdk_externo, "create_charge", create_charge_con_error)

        resultado = pasarela.cobrar(
            monto_centavos=1000, moneda="mxn", referencia="pedido-4"
        )

        assert resultado.exitoso is False
        assert "PROVIDER_DOWN" in resultado.mensaje


class TestReembolso:
    def test_reembolso_exitoso(self, pasarela):
        cobro = pasarela.cobrar(
            monto_centavos=5000, moneda="mxn", referencia="pedido-5"
        )
        reembolso = pasarela.reembolsar(cobro.id_transaccion)

        assert reembolso.exitoso is True
        assert reembolso.id_transaccion == cobro.id_transaccion

    def test_no_permite_reembolsar_dos_veces(self, pasarela):
        cobro = pasarela.cobrar(
            monto_centavos=5000, moneda="mxn", referencia="pedido-6"
        )
        pasarela.reembolsar(cobro.id_transaccion)
        segundo_intento = pasarela.reembolsar(cobro.id_transaccion)

        assert segundo_intento.exitoso is False
        assert "ALREADY_REFUNDED" in segundo_intento.mensaje

    def test_reembolso_de_transaccion_inexistente(self, pasarela):
        resultado = pasarela.reembolsar("id-que-no-existe")

        assert resultado.exitoso is False
        assert "CHARGE_NOT_FOUND" in resultado.mensaje


def test_sdk_externo_requiere_api_key():
    with pytest.raises(ValueError):
        ProveedorPagoExternoSDK(api_key="")
