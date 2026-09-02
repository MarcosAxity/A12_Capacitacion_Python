"""Manejadores de eventos de dominio, ejecutados dentro de la capa de
aplicación (no dentro del dominio, ni en infraestructura).

Reaccionan a OrderCreated sin que el caso de uso principal (CreateOrder)
sepa nada de "notificaciones": queda desacoplado y con una única
responsabilidad (crear la orden).
"""
from __future__ import annotations
from orders.domain.events import OrderCreated

# Log en memoria, útil para inspeccionar en la demo y en pruebas qué se
# publicó, sin depender de un canal real (email/Slack/etc.).
notifications_log: list[str] = []


def send_order_confirmation(event: OrderCreated) -> None:
    message = (
        f"[Notificación] Orden {event.order_id} creada para cliente "
        f"{event.customer_id} por {event.total_amount} {event.currency}."
    )
    notifications_log.append(message)
    print(message)
