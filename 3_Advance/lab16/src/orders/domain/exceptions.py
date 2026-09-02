"""Excepciones de negocio (no técnicas). Viven en el dominio porque
expresan violaciones a las reglas del negocio, no fallos de infraestructura."""


class DomainError(Exception):
    """Excepción base para todos los errores de reglas de negocio."""


class EmptyOrderError(DomainError):
    """Una orden no puede crearse sin al menos un item."""


class InvalidOrderStateError(DomainError):
    """Se intentó una transición de estado inválida."""


class OrderNotFoundError(DomainError):
    """No existe una orden con el identificador solicitado."""
