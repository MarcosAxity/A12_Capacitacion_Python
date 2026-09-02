"""Adaptador de persistencia real: implementa el puerto OrderRepository
sobre SQLAlchemy (async). Traduce entre entidades de dominio (Order,
OrderItem) y modelos ORM (OrderModel, OrderItemModel) en ambas direcciones,
manteniendo el dominio ajeno al ORM.
"""
from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from orders.domain.entities import Order, OrderItem
from orders.domain.value_objects import Money, OrderStatus, ProductRef
from orders.infrastructure.adapters.db.models import OrderItemModel, OrderModel


class SqlAlchemyOrderRepository:
    """Implementa el Protocol OrderRepository usando una AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, order: Order) -> None:
        model = await self._session.get(OrderModel, order.id)
        if model is None:
            model = OrderModel(id=order.id)
            self._session.add(model)
        else:
            # Reemplaza los items existentes para simplificar el mapeo
            # (aceptable dado el tamaño acotado de una orden).
            await self._session.execute(
                delete(OrderItemModel).where(OrderItemModel.order_id == order.id)
            )

        model.customer_id = order.customer_id
        model.status = order.status.value
        model.currency = order.currency
        model.created_at = order.created_at
        model.updated_at = order.updated_at
        model.items = [
            OrderItemModel(
                product_id=item.product.product_id,
                product_name=item.product.name,
                quantity=item.quantity,
                unit_price=item.unit_price.amount,
            )
            for item in order.items
        ]
        await self._session.flush()

    async def get(self, order_id: str) -> Order | None:
        model = await self._session.get(OrderModel, order_id)
        if model is None:
            return None
        return self._to_domain(model)

    async def list(
        self, customer_id: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[Order]:
        stmt = select(OrderModel).order_by(OrderModel.created_at).limit(limit).offset(offset)
        if customer_id is not None:
            stmt = stmt.where(OrderModel.customer_id == customer_id)
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def delete(self, order_id: str) -> bool:
        model = await self._session.get(OrderModel, order_id)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    @staticmethod
    def _to_domain(model: OrderModel) -> Order:
        order = Order(
            customer_id=model.customer_id,
            id=model.id,
            status=OrderStatus(model.status),
            currency=model.currency,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
        order.items = [
            OrderItem(
                product=ProductRef(product_id=i.product_id, name=i.product_name),
                quantity=i.quantity,
                unit_price=Money(i.unit_price, model.currency),
            )
            for i in model.items
        ]
        return order
