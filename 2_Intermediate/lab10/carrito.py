"""
Módulo 10 - TDD
Historia: Como cliente, quiero aplicar un cupón de descuento a mi carrito,
para pagar menos, sin que el total sea nunca negativo ni el descuento
supere el 100%.
"""


class CuponInvalido(Exception):
    """Se lanza cuando el porcentaje de descuento está fuera de rango."""

    pass


class Carrito:
    def __init__(self):
        self._items = []

    def agregar(self, precio: float, cantidad: int):
        if precio < 0 or cantidad < 0:
            raise ValueError("precio y cantidad deben ser >= 0")
        self._items.append(precio * cantidad)

    def total(self) -> float:
        return sum(self._items)

    def aplicar_cupon(self, porcentaje: float, validador_externo=None):
        """
        Aplica un descuento porcentual al total del carrito.

        :param porcentaje: valor entre 0 y 100.
        :param validador_externo: callable opcional (p.ej. servicio de
            validación de cupones) que recibe el porcentaje y puede
            lanzar una excepción si el cupón no es válido en el sistema
            externo.
        """
        if not (0 <= porcentaje <= 100):
            raise CuponInvalido(f"Porcentaje inválido: {porcentaje}")

        if validador_externo:
            validador_externo(porcentaje)

        total_actual = self.total()
        descuento = total_actual * (porcentaje / 100)
        nuevo_total = total_actual - descuento

        # Salvaguarda extra: nunca dejar el carrito en negativo
        self._items = [max(nuevo_total, 0)]
