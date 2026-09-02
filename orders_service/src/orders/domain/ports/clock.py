"""Puerto de reloj: permite inyectar tiempo determinista en pruebas."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    """Adaptador por defecto: usa la hora real del sistema en UTC."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock:
    """Adaptador de prueba: siempre retorna la misma hora fija."""

    def __init__(self, fixed_time: datetime) -> None:
        self._fixed_time = fixed_time

    def now(self) -> datetime:
        return self._fixed_time
