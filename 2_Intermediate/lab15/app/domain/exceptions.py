"""Excepciones propias del dominio. No dependen de HTTP ni de la BD."""


class DomainError(Exception):
    """Excepción base para errores de reglas de negocio."""


class EmptyOrderError(DomainError):
    """Se intentó crear un pedido sin items."""


class InvalidQuantityError(DomainError):
    """Cantidad o precio inválido en una línea de pedido."""


class OrderNotFoundError(DomainError):
    """No existe un pedido con el id solicitado."""
