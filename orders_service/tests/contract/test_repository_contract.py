"""Pruebas de contrato del puerto OrderRepository.

La idea central del testing de contrato en Arquitectura Hexagonal: una
única suite de aserciones se ejecuta contra *todos* los adaptadores que
implementan el mismo puerto (in-memory y SQLAlchemy). Si un adaptador
nuevo se agrega en el futuro, basta con añadirlo a la fixture
parametrizada `repository` para validar que cumple el contrato.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from orders.domain.entities import Order
from orders.domain.value_objects import ProductRef
from orders.infrastructure.adapters.db.in_memory_repository import InMemoryOrderRepository
from orders.infrastructure.adapters.db.models import Base
from orders.infrastructure.adapters.db.session import make_engine, make_session_factory
from orders.infrastructure.adapters.db.sqlalchemy_repository import SqlAlchemyOrderRepository


class _SqlAlchemyRepoWithCommit:
    """Envuelve SqlAlchemyOrderRepository para hacer commit automático,
    de modo que la suite de contrato pueda tratarlo igual que al
    repositorio in-memory (que persiste inmediatamente).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._inner = SqlAlchemyOrderRepository(session)

    async def save(self, order: Order) -> None:
        await self._inner.save(order)
        await self._session.commit()

    async def get(self, order_id: str) -> Order | None:
        return await self._inner.get(order_id)

    async def list(self, customer_id=None, limit=50, offset=0) -> list[Order]:
        return await self._inner.list(customer_id=customer_id, limit=limit, offset=offset)

    async def delete(self, order_id: str) -> bool:
        result = await self._inner.delete(order_id)
        await self._session.commit()
        return result


async def _build_in_memory_repository():
    return InMemoryOrderRepository(), None


async def _build_sqlalchemy_repository():
    engine = make_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = make_session_factory(engine)
    session = session_factory()
    return _SqlAlchemyRepoWithCommit(session), (session, engine)


_ADAPTER_BUILDERS = {
    "in_memory": _build_in_memory_repository,
    "sqlalchemy": _build_sqlalchemy_repository,
}


@pytest_asyncio.fixture(params=["in_memory", "sqlalchemy"])
async def repository(request: pytest.FixtureRequest):
    build = _ADAPTER_BUILDERS[request.param]
    repo, resources = await build()
    yield repo
    if resources is not None:
        session, engine = resources
        await session.close()
        await engine.dispose()


@pytest.mark.contract
class TestOrderRepositoryContract:
    """Cada método de prueba se ejecuta dos veces (una por adaptador),
    gracias a la fixture `repository` parametrizada arriba.
    """

    @pytest_asyncio.fixture(autouse=True)
    async def _setup(self, repository) -> None:
        self.repository = repository

    async def test_save_and_get_roundtrip(self) -> None:
        order = Order.create(customer_id="cust-1")
        order.add_item(ProductRef("prod-1", "Teclado"), 2, Decimal("100.00"))

        await self.repository.save(order)
        fetched = await self.repository.get(order.id)

        assert fetched is not None
        assert fetched.id == order.id
        assert fetched.customer_id == "cust-1"
        assert len(fetched.items) == 1
        assert fetched.items[0].quantity == 2
        assert fetched.total().amount == Decimal("200.00")

    async def test_get_returns_none_when_not_found(self) -> None:
        result = await self.repository.get("non-existent-id")
        assert result is None

    async def test_save_is_idempotent_upsert(self) -> None:
        order = Order.create(customer_id="cust-1")
        await self.repository.save(order)

        order.add_item(ProductRef("prod-1", "Teclado"), 1, Decimal("50.00"))
        await self.repository.save(order)

        fetched = await self.repository.get(order.id)
        assert fetched is not None
        assert len(fetched.items) == 1

    async def test_list_filters_by_customer(self) -> None:
        order_a = Order.create(customer_id="cust-A")
        order_b = Order.create(customer_id="cust-B")
        await self.repository.save(order_a)
        await self.repository.save(order_b)

        result = await self.repository.list(customer_id="cust-A")

        assert len(result) == 1
        assert result[0].customer_id == "cust-A"

    async def test_list_respects_limit_and_offset(self) -> None:
        for _ in range(5):
            await self.repository.save(Order.create(customer_id="cust-paging"))

        page1 = await self.repository.list(customer_id="cust-paging", limit=2, offset=0)
        page2 = await self.repository.list(customer_id="cust-paging", limit=2, offset=2)

        assert len(page1) == 2
        assert len(page2) == 2
        assert {o.id for o in page1}.isdisjoint({o.id for o in page2})

    async def test_delete_removes_order(self) -> None:
        order = Order.create(customer_id="cust-1")
        await self.repository.save(order)

        deleted = await self.repository.delete(order.id)
        fetched = await self.repository.get(order.id)

        assert deleted is True
        assert fetched is None

    async def test_delete_returns_false_when_not_found(self) -> None:
        result = await self.repository.delete("non-existent-id")
        assert result is False
