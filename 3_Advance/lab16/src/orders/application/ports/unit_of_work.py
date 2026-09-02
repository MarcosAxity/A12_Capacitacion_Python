"""Puerto de Unit of Work (UoW).

El UoW agrupa una o más operaciones de repositorio en una sola transacción
atómica, y es responsable de publicar los eventos de dominio generados
DURANTE esa transacción, pero SÓLO si la transacción se confirma (commit).
Si algo falla antes del commit, no se persiste nada ni se publica ningún
evento: se evita el problema clásico de "evento publicado pero dato no
guardado" (o viceversa).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from orders.application.ports.repositories import OrderRepository


class UnitOfWork(ABC):
    orders: OrderRepository

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # Si el bloque `with` termina sin commit explícito (por excepción
        # o por olvido), se hace rollback por seguridad: nunca se publican
        # eventos de una transacción que no fue confirmada.
        self.rollback()

    @abstractmethod
    def commit(self) -> None:
        ...

    @abstractmethod
    def rollback(self) -> None:
        ...
