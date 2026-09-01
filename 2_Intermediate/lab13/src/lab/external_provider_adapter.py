"""
Laboratorio 3: Adapter para proveedor externo
=================================================
Caso de uso real: nuestra aplicacion define una interfaz propia
(PasarelaPago) para procesar cobros. Queremos poder cambiar de proveedor
de pagos (Stripe, PayPal, un banco local, etc.) sin que el resto del
codigo tenga que cambiar.

El problema: cada proveedor externo (SDK de terceros) expone su propia
API, con nombres de metodos, formatos de entrada/salida y manejo de
errores distintos entre si (y distintos a los que definimos nosotros).

La solucion: el patron Adapter. Definimos:
  1. Una interfaz propia (`PasarelaPago`) que el resto de la app consume.
  2. Un SDK externo simulado (`ProveedorPagoExternoSDK`) con una interfaz
     incompatible, tal como vendria de una libreria de terceros real.
  3. Un Adapter (`AdaptadorProveedorExterno`) que traduce entre ambas
     interfaces.

Esto tambien facilita las pruebas: se puede probar el Adapter contra un
"SDK falso" controlado, sin llamar a un servicio real.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# 1) Interfaz propia (lo que el resto de nuestra aplicacion espera usar)
# ---------------------------------------------------------------------------


@dataclass
class ResultadoPago:
    exitoso: bool
    id_transaccion: str
    mensaje: str = ""


class PasarelaPago(ABC):
    """Interfaz (Target) que define el contrato que nuestra aplicacion
    espera de cualquier pasarela de pago, sin importar el proveedor real
    detras."""

    @abstractmethod
    def cobrar(
        self, monto_centavos: int, moneda: str, referencia: str
    ) -> ResultadoPago: ...

    @abstractmethod
    def reembolsar(self, id_transaccion: str) -> ResultadoPago: ...


# ---------------------------------------------------------------------------
# 2) SDK externo simulado (Adaptee): interfaz incompatible que NO podemos
#    modificar porque pertenece a una libreria/proveedor de terceros.
# ---------------------------------------------------------------------------


class ProveedorPagoExternoSDK:
    """Simula el SDK de un proveedor de pagos de terceros.

    Notese que:
      - Los montos se manejan como *string* en formato "12.34" (no en
        centavos como enteros).
      - Los metodos tienen nombres/formas distintas a nuestra interfaz.
      - Los errores se devuelven como diccionarios con codigos propios,
        en vez de excepciones o del dataclass ResultadoPago.
    """

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Se requiere una api_key para el SDK externo")
        self._api_key = api_key
        self._transacciones: dict[str, dict] = {}
        self._contador = 0

    def create_charge(
        self, amount_str: str, currency_code: str, external_ref: str
    ) -> dict:
        """Formato de entrada/salida propio del proveedor externo."""
        try:
            monto = float(amount_str)
        except ValueError:
            return {"ok": False, "error_code": "INVALID_AMOUNT", "charge_id": None}

        if monto <= 0:
            return {
                "ok": False,
                "error_code": "AMOUNT_MUST_BE_POSITIVE",
                "charge_id": None,
            }

        self._contador += 1
        charge_id = f"ext-charge-{self._contador}"
        self._transacciones[charge_id] = {
            "amount": monto,
            "currency": currency_code,
            "ref": external_ref,
            "refunded": False,
        }
        return {"ok": True, "error_code": None, "charge_id": charge_id}

    def refund_charge(self, charge_id: str) -> dict:
        transaccion = self._transacciones.get(charge_id)
        if transaccion is None:
            return {"ok": False, "error_code": "CHARGE_NOT_FOUND"}
        if transaccion["refunded"]:
            return {"ok": False, "error_code": "ALREADY_REFUNDED"}
        transaccion["refunded"] = True
        return {"ok": True, "error_code": None}


# ---------------------------------------------------------------------------
# 3) Adapter: traduce entre nuestra interfaz (PasarelaPago) y el SDK
#    externo (ProveedorPagoExternoSDK).
# ---------------------------------------------------------------------------


class AdaptadorProveedorExterno(PasarelaPago):
    """Adapta ProveedorPagoExternoSDK a la interfaz PasarelaPago que
    consume el resto de la aplicacion."""

    def __init__(self, sdk_externo: ProveedorPagoExternoSDK):
        self._sdk = sdk_externo

    def cobrar(
        self, monto_centavos: int, moneda: str, referencia: str
    ) -> ResultadoPago:
        if monto_centavos <= 0:
            return ResultadoPago(
                exitoso=False, id_transaccion="", mensaje="El monto debe ser positivo"
            )

        # Traduccion de formato: centavos (int) -> string decimal "12.34"
        monto_decimal_str = f"{monto_centavos / 100:.2f}"

        respuesta = self._sdk.create_charge(
            amount_str=monto_decimal_str,
            currency_code=moneda.upper(),
            external_ref=referencia,
        )

        if not respuesta["ok"]:
            return ResultadoPago(
                exitoso=False,
                id_transaccion="",
                mensaje=f"Error del proveedor: {respuesta['error_code']}",
            )

        return ResultadoPago(
            exitoso=True,
            id_transaccion=respuesta["charge_id"],
            mensaje="Cobro procesado correctamente",
        )

    def reembolsar(self, id_transaccion: str) -> ResultadoPago:
        respuesta = self._sdk.refund_charge(id_transaccion)
        if not respuesta["ok"]:
            return ResultadoPago(
                exitoso=False,
                id_transaccion=id_transaccion,
                mensaje=f"Error del proveedor: {respuesta['error_code']}",
            )
        return ResultadoPago(
            exitoso=True,
            id_transaccion=id_transaccion,
            mensaje="Reembolso procesado correctamente",
        )
