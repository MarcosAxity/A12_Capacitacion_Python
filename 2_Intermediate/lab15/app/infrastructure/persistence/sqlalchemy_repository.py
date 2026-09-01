"""
ADAPTADOR de infraestructura: repositorio con SQLAlchemy.

Implementa el mismo puerto (`OrderRepositoryPort`) que el repositorio en
memoria, pero persistiendo en una base de datos relacional real a través
de SQLAlchemy. Es intercambiable 1:1 con `InMemoryOrderRepository`: el
caso de uso `CreateOrderUseCase` no necesita saber cuál de los dos está
usando.

Aquí es donde se traduce entre:
  - Entidad de dominio  (app.domain.entities.Order)
  - Modelo ORM           (app.infrastructure.db.models.OrderModel)
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.entities import Order, OrderItem, OrderStatus
from app.infrastructure.db.models import OrderItemModel, OrderModel
from sqlalchemy import select
from sqlalchemy.orm import Session


class SqlAlchemyOrderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, order: Order) -> None:
        model = self._session.get(OrderModel, order.id)
        if model is None:
            model = OrderModel(
                id=order.id, customer_id=order.customer_id, status=order.status.value
            )
            self._session.add(model)
        else:
            model.status = order.status.value
            model.items.clear()

        model.items = [
            OrderItemModel(
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in order.items
        ]
        self._session.commit()

    def get_by_id(self, order_id: str) -> Order | None:
        model = self._session.get(OrderModel, order_id)
        if model is None:
            return None
        return _model_to_entity(model)

    def list_all(self) -> list[Order]:
        models = self._session.scalars(select(OrderModel)).all()
        return [_model_to_entity(model) for model in models]


def _model_to_entity(model: OrderModel) -> Order:
    order = Order(
        customer_id=model.customer_id,
        items=[
            OrderItem(
                product_id=i.product_id,
                quantity=i.quantity,
                unit_price=Decimal(str(i.unit_price)),
            )
            for i in model.items
        ],
        id=model.id,
    )
    order.status = OrderStatus(model.status)
    return order
