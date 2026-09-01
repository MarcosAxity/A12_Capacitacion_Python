"""Puertos del dominio, expresados como `typing.Protocol`.

DIP (Dependency Inversion Principle):
    El dominio (services.py) depende de estas ABSTRACCIONES, nunca de
    una implementación concreta (SQL, memoria, SMTP, etc.). Las
    implementaciones concretas viven en `infrastructure/` y dependen
    de estos Protocols, invirtiendo la dirección clásica de la
    dependencia.

ISP (Interface Segregation Principle):
    En vez de un único "IOrderStorageAndNotificationAndDiscount" gigante,
    se definen protocolos pequeños y enfocados (Repository, Notifier,
    DiscountPolicy). Cada implementación concreta solo debe cumplir el
    contrato que realmente usa; nadie se ve forzado a implementar
    métodos que no necesita.

Usar `Protocol` (en vez de ABC) permite *duck typing estático*: una
clase implementa el puerto con solo tener los métodos correctos, sin
heredar explícitamente. Esto es lo más "pythonic" de aplicar DIP.
"""

from typing import List, Optional, Protocol

from .models import Order


class OrderRepository(Protocol):
    """Puerto de persistencia de pedidos (contrato pequeño y explícito)."""

    def add(self, order: Order) -> None: ...

    def get(self, order_id: str) -> Optional[Order]: ...

    def list_all(self) -> List[Order]: ...

    def update(self, order: Order) -> None: ...


class Notifier(Protocol):
    """Puerto de notificación. Un único método: ISP en su máxima expresión."""

    def send(self, to: str, message: str) -> None: ...


class DiscountPolicy(Protocol):
    """Puerto de política de descuento (usado también para ilustrar OCP)."""

    def apply(self, total: float) -> float: ...
