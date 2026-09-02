"""Presenter: da formato de salida a los DTOs de la aplicación.

Mantiene el "cómo se ve la respuesta" (dict listo para JSON/consola, en
este ejemplo) separado del "qué hace la aplicación" (los casos de uso).
Si mañana se necesita un presenter para HTML o para XML, se agrega uno
nuevo sin tocar los casos de uso ni el dominio.
"""
from __future__ import annotations
from typing import Any, Dict, List
from orders.application.dto import OrderResponse
from orders.domain.exceptions import DomainError


class OrderPresenter:
    def present_order(self, response: OrderResponse) -> Dict[str, Any]:
        return {
            "id": response.id,
            "customer_id": response.customer_id,
            "status": response.status,
            "items": [
                {
                    "product_id": i.product_id,
                    "quantity": i.quantity,
                    "unit_price": str(i.unit_price),
                    "subtotal": str(i.subtotal),
                }
                for i in response.items
            ],
            "total": f"{response.total_amount} {response.currency}",
        }

    def present_order_list(self, responses: List[OrderResponse]) -> Dict[str, Any]:
        return {"orders": [self.present_order(r) for r in responses]}

    def present_error(self, error: Exception) -> Dict[str, Any]:
        status = "domain_error" if isinstance(error, DomainError) else "error"
        return {"error": status, "message": str(error)}
