"""Servicio de aplicación/dominio.

SRP (Single Responsibility Principle):
    `OrderService` tiene una única responsabilidad: orquestar el caso
    de uso "gestionar pedidos" (crear, descontar, notificar, listar).
    NO sabe cómo se persiste un pedido (eso es del repositorio), NO
    sabe cómo se envía un mensaje (eso es del notifier) y NO sabe cómo
    se calcula un descuento (eso es de la política). Cada una de esas
    responsabilidades vive en su propia clase con su propia razón de
    cambio.

DIP (Dependency Inversion Principle):
    El constructor recibe `OrderRepository`, `Notifier` y
    `DiscountPolicy` -- todos son `Protocol` definidos en `ports.py` y
    `policies.py`. `OrderService` nunca importa `sqlite3` ni clases
    concretas de infraestructura. Esto permite:
      1) Cambiar de memoria a SQL sin tocar una sola línea de este
         archivo (ver `infrastructure/`).
      2) Testear el servicio con un repositorio falso ultra simple,
         sin base de datos (ver `tests/test_service_srp.py`).

LSP (Liskov Substitution Principle):
    Como `OrderService` solo conoce el contrato `OrderRepository`,
    CUALQUIER implementación que cumpla ese contrato (memoria, SQL,
    o una futura implementación en Mongo/Redis) debe poder
    sustituirse sin romper el comportamiento esperado por el
    servicio. Los tests de contrato en
    `tests/test_lsp_contract.py` verifican justamente eso: se corre
    la MISMA batería de pruebas contra cada implementación.
"""

from typing import List

from .models import Order, OrderStatus
from .policies import NoDiscount
from .ports import DiscountPolicy, Notifier, OrderRepository


class OrderNotFoundError(Exception):
    pass


class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
        notifier: Notifier,
        discount_policy: DiscountPolicy | None = None,
    ) -> None:
        self._repository = repository
        self._notifier = notifier
        self._discount_policy: DiscountPolicy = discount_policy or NoDiscount()

    def place_order(self, customer: str, total: float) -> Order:
        order = Order(customer=customer, total=total)
        self._repository.add(order)
        return order

    def apply_discount(self, order_id: str) -> Order:
        order = self._get_or_raise(order_id)
        order.total = self._discount_policy.apply(order.total)
        order.status = OrderStatus.DISCOUNTED
        self._repository.update(order)
        return order

    def notify_customer(self, order_id: str, message: str | None = None) -> Order:
        order = self._get_or_raise(order_id)
        text = message or f"Tu pedido {order.id} por {order.total} fue procesado."
        self._notifier.send(order.customer, text)
        order.status = OrderStatus.NOTIFIED
        self._repository.update(order)
        return order

    def list_orders(self) -> List[Order]:
        return self._repository.list_all()

    def _get_or_raise(self, order_id: str) -> Order:
        order = self._repository.get(order_id)
        if order is None:
            raise OrderNotFoundError(f"Pedido {order_id} no encontrado")
        return order
