"""Pruebas del caso de uso CreateOrder usando los adaptadores en memoria.
Ilustra que el caso de uso puede probarse aislado de cualquier framework
web y de cualquier base de datos real."""
from decimal import Decimal

from orders.application.dto import CreateOrderItemRequest, CreateOrderRequest
from orders.application.use_cases.create_order import CreateOrderUseCase
from orders.domain.events import OrderCreated
from orders.infrastructure.events.in_memory_event_bus import InMemoryEventBus
from orders.infrastructure.persistence.in_memory_repository import InMemoryOrderRepository
from orders.infrastructure.persistence.in_memory_unit_of_work import InMemoryUnitOfWork


def build_use_case():
    repo = InMemoryOrderRepository()
    bus = InMemoryEventBus()
    published = []
    bus.subscribe(OrderCreated, lambda e: published.append(e))
    uow = InMemoryUnitOfWork(repo, bus)
    return CreateOrderUseCase(uow), repo, published


def test_create_order_use_case_persists_order_and_publishes_event():
    use_case, repo, published = build_use_case()

    request = CreateOrderRequest(
        customer_id="c1",
        items=[CreateOrderItemRequest(product_id="p1", quantity=3, unit_price=Decimal("2.00"))],
    )
    response = use_case.execute(request)

    assert response.total_amount == Decimal("6.00")
    assert repo.get(response.id) is not None
    assert len(published) == 1
    assert published[0].order_id == response.id
