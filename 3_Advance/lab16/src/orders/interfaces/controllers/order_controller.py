"""Controlador: puerta de entrada desde el exterior (CLI, HTTP, etc.).

Traduce la entrada cruda (un dict, que podría venir de un JSON de HTTP o
de argumentos de CLI) a un Request DTO de la capa de aplicación, invoca el
caso de uso correspondiente y delega el formateo de salida al Presenter.
No contiene ninguna regla de negocio: solo coordina.
"""
from __future__ import annotations
from decimal import Decimal
from typing import Any, Dict

from orders.application.dto import CreateOrderItemRequest, CreateOrderRequest
from orders.application.use_cases.create_order import CreateOrderUseCase
from orders.application.use_cases.get_order import GetOrderUseCase
from orders.application.use_cases.list_orders import ListOrdersUseCase
from orders.domain.exceptions import DomainError, OrderNotFoundError
from orders.interfaces.presenters.order_presenter import OrderPresenter


class OrderController:
    def __init__(
        self,
        create_order_uc: CreateOrderUseCase,
        get_order_uc: GetOrderUseCase,
        list_orders_uc: ListOrdersUseCase,
        presenter: OrderPresenter,
    ):
        self._create_order_uc = create_order_uc
        self._get_order_uc = get_order_uc
        self._list_orders_uc = list_orders_uc
        self._presenter = presenter

    def create_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            request = CreateOrderRequest(
                customer_id=payload["customer_id"],
                items=[
                    CreateOrderItemRequest(
                        product_id=i["product_id"],
                        quantity=int(i["quantity"]),
                        unit_price=Decimal(str(i["unit_price"])),
                    )
                    for i in payload["items"]
                ],
            )
            response = self._create_order_uc.execute(request)
            return self._presenter.present_order(response)
        except DomainError as e:
            return self._presenter.present_error(e)

    def get_order(self, order_id: str) -> Dict[str, Any]:
        try:
            response = self._get_order_uc.execute(order_id)
            return self._presenter.present_order(response)
        except OrderNotFoundError as e:
            return self._presenter.present_error(e)

    def list_orders(self) -> Dict[str, Any]:
        responses = self._list_orders_uc.execute()
        return self._presenter.present_order_list(responses)
