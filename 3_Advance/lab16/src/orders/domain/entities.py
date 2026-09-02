"""Entidades del dominio: objetos con identidad y reglas de negocio propias.

En Clean Architecture, las Entidades son el círculo más interno: no dependen
de ninguna otra capa (ni aplicación, ni infraestructura, ni frameworks web o
de persistencia). Encapsulan las reglas de negocio más generales y estables.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

from orders.domain.value_objects import Money, OrderStatus
from orders.domain.events import DomainEvent, OrderCreated
from orders.domain.exceptions import EmptyOrderError, InvalidOrderStateError


@dataclass
class OrderItem:
    product_id: str
    quantity: int
    unit_price: Money

    def subtotal(self) -> Money:
        return self.unit_price.multiply(self.quantity)


@dataclass
class Order:
    """Entidad Order (agregado raíz del contexto de órdenes).

    Registra sus propios eventos de dominio en una lista interna; es el
    Unit of Work (capa de infraestructura) quien luego los recolecta y
    los publica, pero la entidad no sabe nada de eso: solo los produce.
    """

    id: str
    customer_id: str
    items: List[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.CREATED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _domain_events: List[DomainEvent] = field(default_factory=list, repr=False)

    @classmethod
    def create(cls, customer_id: str, items: List[OrderItem]) -> "Order":
        """Factory method: único punto de entrada válido para crear una
        Order, garantizando que la regla 'no hay orden vacía' se cumpla
        siempre, sin importar quién la invoque."""
        if not items:
            raise EmptyOrderError("Una orden debe tener al menos un item.")

        order = cls(id=str(uuid.uuid4()), customer_id=customer_id, items=items)
        order._domain_events.append(
            OrderCreated(
                order_id=order.id,
                customer_id=order.customer_id,
                total_amount=order.total().amount,
                currency=order.total().currency,
            )
        )
        return order

    def total(self) -> Money:
        if not self.items:
            return Money(0, "USD")
        currency = self.items[0].unit_price.currency
        total = sum((item.subtotal().amount for item in self.items), start=0)
        return Money(total, currency)

    def cancel(self) -> None:
        if self.status == OrderStatus.CANCELLED:
            raise InvalidOrderStateError("La orden ya está cancelada.")
        self.status = OrderStatus.CANCELLED

    def pull_domain_events(self) -> List[DomainEvent]:
        """Devuelve los eventos pendientes y limpia la lista interna.
        Lo invoca el Unit of Work al hacer commit, nunca el dominio mismo."""
        events, self._domain_events = self._domain_events, []
        return events
