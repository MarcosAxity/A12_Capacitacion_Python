"""Entidades del dominio.

`Order` es el Aggregate Root: toda mutación del pedido y de sus items pasa
por sus métodos, que protegen los invariantes de negocio. `OrderItem` es
una entidad interna al agregado (no se accede ni se persiste de forma
independiente fuera de `Order`).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from orders.domain.events import (
    DomainEvent,
    OrderCancelled,
    OrderConfirmed,
    OrderCreated,
    OrderItemAdded,
)
from orders.domain.exceptions import (
    EmptyOrderError,
    InvalidItemQuantityError,
    InvalidOrderStateError,
)
from orders.domain.value_objects import Money, OrderStatus, ProductRef, new_order_id


@dataclass(slots=True)
class OrderItem:
    """Línea de un pedido. Entidad hija, sin identidad propia fuera del agregado."""

    product: ProductRef
    quantity: int
    unit_price: Money

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise InvalidItemQuantityError(self.quantity)

    @property
    def subtotal(self) -> Money:
        return self.unit_price * self.quantity


@dataclass(slots=True)
class Order:
    """Aggregate Root del dominio Orders.

    Encapsula el estado y las reglas de negocio de un pedido: alta,
    adición de items, confirmación y cancelación. Toda transición inválida
    lanza una excepción de dominio explícita en lugar de dejar el objeto
    en un estado inconsistente.
    """

    customer_id: str
    id: str = field(default_factory=new_order_id)
    status: OrderStatus = OrderStatus.CREATED
    items: list[OrderItem] = field(default_factory=list)
    currency: str = "MXN"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    _events: list[DomainEvent] = field(default_factory=list, repr=False)

    @classmethod
    def create(cls, customer_id: str, currency: str = "MXN") -> Order:
        if not customer_id.strip():
            raise ValueError("customer_id no puede estar vacío")
        order = cls(customer_id=customer_id, currency=currency)
        order._record(OrderCreated(order_id=order.id, customer_id=customer_id))
        return order

    def add_item(self, product: ProductRef, quantity: int, unit_price: Decimal) -> None:
        if self.status != OrderStatus.CREATED:
            raise InvalidOrderStateError(self.status.value, "add_item")
        item = OrderItem(
            product=product,
            quantity=quantity,
            unit_price=Money(unit_price, self.currency),
        )
        self.items.append(item)
        self._touch()
        self._record(
            OrderItemAdded(
                order_id=self.id,
                product_id=product.product_id,
                quantity=quantity,
                unit_price=item.unit_price.amount,
            )
        )

    def total(self) -> Money:
        total = Money.zero(self.currency)
        for item in self.items:
            total = total + item.subtotal
        return total

    def confirm(self) -> None:
        if not self.items:
            raise EmptyOrderError()
        if not self.status.can_transition_to(OrderStatus.CONFIRMED):
            raise InvalidOrderStateError(self.status.value, OrderStatus.CONFIRMED.value)
        self.status = OrderStatus.CONFIRMED
        self._touch()
        self._record(OrderConfirmed(order_id=self.id, total_amount=self.total().amount))

    def cancel(self, reason: str = "") -> None:
        if not self.status.can_transition_to(OrderStatus.CANCELLED):
            raise InvalidOrderStateError(self.status.value, OrderStatus.CANCELLED.value)
        self.status = OrderStatus.CANCELLED
        self._touch()
        self._record(OrderCancelled(order_id=self.id, reason=reason))

    def pull_events(self) -> list[DomainEvent]:
        """Devuelve y limpia los eventos pendientes de publicar (patrón Outbox simple)."""
        events, self._events = self._events, []
        return events

    def _record(self, event: DomainEvent) -> None:
        self._events.append(event)

    def _touch(self) -> None:
        self.updated_at = datetime.now(UTC)
