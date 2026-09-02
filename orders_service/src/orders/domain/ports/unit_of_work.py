"""Puerto Unit of Work: agrupa operaciones de persistencia en una transacción.

Se usa como context manager asíncrono. El commit debe ser explícito; si el
bloque `async with` termina por excepción, el adaptador debe hacer rollback.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from orders.domain.ports.repository import OrderRepository


@runtime_checkable
class UnitOfWork(Protocol):
    orders: OrderRepository

    async def __aenter__(self) -> UnitOfWork: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
