"""
PRUEBAS DE CONTRATO.

El objetivo de una prueba de contrato es garantizar que TODOS los
adaptadores que implementan un mismo puerto (`OrderRepositoryPort`) se
comportan de forma equivalente desde el punto de vista del caso de uso.

Aquí definimos una única batería de pruebas (`RepositoryContractTests`)
y la ejecutamos contra:
  1. `InMemoryOrderRepository`
  2. `SqlAlchemyOrderRepository` (usando SQLite en memoria, para no
     dejar archivos de BD tirados al correr los tests)

Si mañana agregamos un adaptador de MongoDB o de otro motor SQL, basta
con agregar un nuevo fixture que apunte a la misma clase de pruebas.
"""

from decimal import Decimal

import pytest
from app.domain.entities import Order, OrderItem
from app.infrastructure.db.models import Base
from app.infrastructure.persistence.memory_repository import InMemoryOrderRepository
from app.infrastructure.persistence.sqlalchemy_repository import (
    SqlAlchemyOrderRepository,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def make_order(customer_id: str = "cust-1") -> Order:
    return Order(
        customer_id=customer_id,
        items=[
            OrderItem(product_id="SKU-1", quantity=2, unit_price=Decimal("9.99")),
            OrderItem(product_id="SKU-2", quantity=1, unit_price=Decimal("100.00")),
        ],
    )


class RepositoryContractTests:
    """
    Clase base con el contrato. No hereda de nada de pytest para no ser
    recolectada directamente: las subclases concretas (una por adaptador)
    son las que pytest efectivamente ejecuta.
    """

    @pytest.fixture
    def repository(self):
        raise NotImplementedError  # cada subclase provee su propio fixture

    def test_save_and_get_by_id_returns_equivalent_order(self, repository):
        order = make_order()
        repository.save(order)

        recovered = repository.get_by_id(order.id)

        assert recovered is not None
        assert recovered.id == order.id
        assert recovered.customer_id == order.customer_id
        assert recovered.total == order.total
        assert len(recovered.items) == len(order.items)

    def test_get_by_id_returns_none_when_not_found(self, repository):
        assert repository.get_by_id("no-existe") is None

    def test_list_all_returns_every_saved_order(self, repository):
        order_1 = make_order("cust-1")
        order_2 = make_order("cust-2")
        repository.save(order_1)
        repository.save(order_2)

        all_orders = repository.list_all()

        assert {o.id for o in all_orders} == {order_1.id, order_2.id}

    def test_save_is_idempotent_for_same_order_id(self, repository):
        order = make_order()
        repository.save(order)
        repository.save(order)  # guardar dos veces no debe duplicar

        assert len(repository.list_all()) == 1


class TestInMemoryOrderRepositoryContract(RepositoryContractTests):
    @pytest.fixture
    def repository(self):
        return InMemoryOrderRepository()


class TestSqlAlchemyOrderRepositoryContract(RepositoryContractTests):
    @pytest.fixture
    def repository(self):
        # SQLite en memoria, aislado por test: rápido y sin dejar archivos.
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine)()
        yield SqlAlchemyOrderRepository(session)
        session.close()
