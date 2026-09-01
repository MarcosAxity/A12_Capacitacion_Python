"""Verificación de LSP (Liskov Substitution Principle).

Idea central: si `InMemoryOrderRepository` y `SqlOrderRepository`
cumplen realmente el contrato `OrderRepository`, entonces la MISMA
batería de pruebas debe pasar sin cambios para ambas. Si una de las
dos rompe una precondición/poscondición implícita del contrato (por
ejemplo, lanza una excepción distinta, o devuelve algo diferente ante
la misma entrada), estas pruebas lo detectan: eso sería una violación
de LSP.

Se usa un fixture parametrizado con `pytest.fixture(params=...)` para
que cada test se ejecute una vez por implementación.
"""

import pytest
from src.domain.models import Order, OrderStatus
from src.infrastructure.memory_repository import InMemoryOrderRepository
from src.infrastructure.sql_repository import SqlOrderRepository


@pytest.fixture(params=["memory", "sql"])
def repository(request):
    """Provee cada implementación del puerto `OrderRepository` de
    forma intercambiable. Agregar una tercera implementación (ej.
    Mongo) solo requiere sumarla a `params`; los tests no cambian."""
    if request.param == "memory":
        return InMemoryOrderRepository()
    if request.param == "sql":
        return SqlOrderRepository(":memory:")
    raise ValueError(request.param)


class TestOrderRepositoryContract:
    """Suite de contrato: válida para CUALQUIER OrderRepository."""

    def test_get_inexistente_devuelve_none(self, repository):
        assert repository.get("no-existe") is None

    def test_add_y_get_devuelve_el_mismo_pedido(self, repository):
        order = Order(customer="lucia@example.com", total=100.0)
        repository.add(order)

        recuperado = repository.get(order.id)

        assert recuperado is not None
        assert recuperado.id == order.id
        assert recuperado.customer == order.customer
        assert recuperado.total == order.total
        assert recuperado.status == OrderStatus.CREATED

    def test_list_all_incluye_todos_los_agregados(self, repository):
        o1 = Order(customer="a@example.com", total=10.0)
        o2 = Order(customer="b@example.com", total=20.0)
        repository.add(o1)
        repository.add(o2)

        ids = {o.id for o in repository.list_all()}

        assert {o1.id, o2.id} <= ids

    def test_update_modifica_el_pedido_existente(self, repository):
        order = Order(customer="c@example.com", total=50.0)
        repository.add(order)

        order.total = 45.0
        order.status = OrderStatus.DISCOUNTED
        repository.update(order)

        actualizado = repository.get(order.id)
        assert actualizado.total == 45.0
        assert actualizado.status == OrderStatus.DISCOUNTED

    def test_update_de_pedido_inexistente_lanza_keyerror(self, repository):
        fantasma = Order(customer="x@example.com", total=1.0)
        with pytest.raises(KeyError):
            repository.update(fantasma)
