"""
Capa de APLICACIÓN: casos de uso y orquestación.

Un caso de uso:
  1. Recibe un DTO de entrada.
  2. Construye/recupera entidades de dominio y aplica reglas de negocio.
  3. Usa PUERTOS (interfaces) para persistir y notificar, sin saber nada
     de SQL, HTTP ni de ningún detalle de infraestructura concreto.
  4. Devuelve un DTO de salida.

El caso de uso depende de abstracciones (OrderRepositoryPort,
NotificationPort), nunca de una implementación concreta. Esto es lo que
permite "enchufar" adaptadores en memoria, SQLAlchemy, HTTP simulado,
etc. sin modificar ni una línea de esta clase (Open/Closed Principle).
"""

from __future__ import annotations

from app.application.dtos import CreateOrderInputDTO, OrderItemDTO, OrderOutputDTO
from app.domain.entities import Order, OrderItem
from app.domain.exceptions import OrderNotFoundError
from app.domain.ports import NotificationPort, OrderRepositoryPort


class CreateOrderUseCase:
    """Caso de uso: crear un pedido nuevo, persistirlo y notificarlo."""

    def __init__(
        self, repository: OrderRepositoryPort, notifier: NotificationPort
    ) -> None:
        # Inyección de dependencias por constructor: el caso de uso recibe
        # los PUERTOS ya resueltos (con su adaptador concreto por detrás),
        # nunca los construye él mismo.
        self._repository = repository
        self._notifier = notifier

    def execute(self, input_dto: CreateOrderInputDTO) -> OrderOutputDTO:
        # 1) Traducimos el DTO de entrada a objetos de dominio.
        domain_items = [
            OrderItem(
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in input_dto.items
        ]

        # 2) Creamos la entidad: aquí se validan las reglas de negocio
        #    (pedido no vacío, cantidades válidas, etc.)
        order = Order(customer_id=input_dto.customer_id, items=domain_items)

        # 3) Persistimos a través del puerto (no sabemos si es SQL o memoria).
        self._repository.save(order)

        # 4) Notificamos a través del puerto (no sabemos si es HTTP real o simulado).
        self._notifier.notify_order_created(order)

        # 5) Traducimos la entidad de vuelta a un DTO de salida.
        return _order_to_output_dto(order)


class GetOrderUseCase:
    """Caso de uso auxiliar: consultar un pedido por id (para el laboratorio/API)."""

    def __init__(self, repository: OrderRepositoryPort) -> None:
        self._repository = repository

    def execute(self, order_id: str) -> OrderOutputDTO:
        order = self._repository.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"No existe el pedido {order_id}")
        return _order_to_output_dto(order)


def _order_to_output_dto(order: Order) -> OrderOutputDTO:
    return OrderOutputDTO(
        id=order.id,
        customer_id=order.customer_id,
        status=order.status.value,
        total=order.total,
        items=[
            OrderItemDTO(
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in order.items
        ],
    )
