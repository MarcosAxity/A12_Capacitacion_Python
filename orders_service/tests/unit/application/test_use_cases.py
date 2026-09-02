"""Pruebas unitarias de casos de uso, usando los adaptadores in-memory
(fakes) de los puertos. No se toca base de datos ni HTTP.
"""
from decimal import Decimal

import pytest

from orders.application.dto import AddItemInput, CreateOrderInput
from orders.application.use_cases import (
    AddItemToOrderUseCase,
    CancelOrderUseCase,
    ConfirmOrderUseCase,
    CreateOrderUseCase,
    GetOrderUseCase,
    ListOrdersUseCase,
)
from orders.domain.exceptions import EmptyOrderError, OrderNotFoundError
from orders.infrastructure.adapters.db.in_memory_repository import InMemoryOrderRepository
from orders.infrastructure.adapters.events.publishers import InMemoryEventPublisher


@pytest.fixture
def repository() -> InMemoryOrderRepository:
    return InMemoryOrderRepository()


@pytest.fixture
def publisher() -> InMemoryEventPublisher:
    return InMemoryEventPublisher()


@pytest.mark.unit
class TestCreateOrderUseCase:
    async def test_creates_order_and_publishes_event(
        self, repository: InMemoryOrderRepository, publisher: InMemoryEventPublisher
    ) -> None:
        use_case = CreateOrderUseCase(repository=repository, event_publisher=publisher)

        dto = await use_case.execute(CreateOrderInput(customer_id="cust-1"))

        assert dto.customer_id == "cust-1"
        assert dto.status == "created"
        stored = await repository.get(dto.id)
        assert stored is not None
        assert len(publisher.published) == 1


@pytest.mark.unit
class TestAddItemToOrderUseCase:
    async def test_adds_item_to_existing_order(
        self, repository: InMemoryOrderRepository, publisher: InMemoryEventPublisher
    ) -> None:
        create_uc = CreateOrderUseCase(repository=repository, event_publisher=publisher)
        order_dto = await create_uc.execute(CreateOrderInput(customer_id="cust-1"))

        add_uc = AddItemToOrderUseCase(repository=repository, event_publisher=publisher)
        result = await add_uc.execute(
            AddItemInput(
                order_id=order_dto.id,
                product_id="prod-1",
                product_name="Teclado",
                quantity=2,
                unit_price=Decimal("199.99"),
            )
        )

        assert len(result.items) == 1
        assert result.total_amount == Decimal("399.98")

    async def test_raises_when_order_does_not_exist(
        self, repository: InMemoryOrderRepository, publisher: InMemoryEventPublisher
    ) -> None:
        use_case = AddItemToOrderUseCase(repository=repository, event_publisher=publisher)
        with pytest.raises(OrderNotFoundError):
            await use_case.execute(
                AddItemInput(
                    order_id="does-not-exist",
                    product_id="prod-1",
                    product_name="Teclado",
                    quantity=1,
                    unit_price=Decimal("10"),
                )
            )


@pytest.mark.unit
class TestConfirmAndCancelOrderUseCases:
    async def test_confirm_order_with_items(
        self, repository: InMemoryOrderRepository, publisher: InMemoryEventPublisher
    ) -> None:
        create_uc = CreateOrderUseCase(repository=repository, event_publisher=publisher)
        order_dto = await create_uc.execute(CreateOrderInput(customer_id="cust-1"))
        add_uc = AddItemToOrderUseCase(repository=repository, event_publisher=publisher)
        await add_uc.execute(
            AddItemInput(order_dto.id, "prod-1", "Teclado", 1, Decimal("100"))
        )

        confirm_uc = ConfirmOrderUseCase(repository=repository, event_publisher=publisher)
        result = await confirm_uc.execute(order_dto.id)

        assert result.status == "confirmed"

    async def test_confirm_empty_order_raises(
        self, repository: InMemoryOrderRepository, publisher: InMemoryEventPublisher
    ) -> None:
        create_uc = CreateOrderUseCase(repository=repository, event_publisher=publisher)
        order_dto = await create_uc.execute(CreateOrderInput(customer_id="cust-1"))

        confirm_uc = ConfirmOrderUseCase(repository=repository, event_publisher=publisher)
        with pytest.raises(EmptyOrderError):
            await confirm_uc.execute(order_dto.id)

    async def test_cancel_order(
        self, repository: InMemoryOrderRepository, publisher: InMemoryEventPublisher
    ) -> None:
        create_uc = CreateOrderUseCase(repository=repository, event_publisher=publisher)
        order_dto = await create_uc.execute(CreateOrderInput(customer_id="cust-1"))

        cancel_uc = CancelOrderUseCase(repository=repository, event_publisher=publisher)
        result = await cancel_uc.execute(order_dto.id, reason="test")

        assert result.status == "cancelled"


@pytest.mark.unit
class TestQueryUseCases:
    async def test_get_order_raises_when_missing(
        self, repository: InMemoryOrderRepository
    ) -> None:
        use_case = GetOrderUseCase(repository=repository)
        with pytest.raises(OrderNotFoundError):
            await use_case.execute("missing")

    async def test_list_orders_filters_by_customer(
        self, repository: InMemoryOrderRepository, publisher: InMemoryEventPublisher
    ) -> None:
        create_uc = CreateOrderUseCase(repository=repository, event_publisher=publisher)
        await create_uc.execute(CreateOrderInput(customer_id="cust-1"))
        await create_uc.execute(CreateOrderInput(customer_id="cust-2"))

        list_uc = ListOrdersUseCase(repository=repository)
        result = await list_uc.execute(customer_id="cust-1")

        assert len(result) == 1
        assert result[0].customer_id == "cust-1"
