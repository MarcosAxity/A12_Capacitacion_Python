"""
ADAPTADOR de infraestructura: notificador HTTP (simulado).

En un sistema real, este adaptador haría un `requests.post(url, json=...)`
hacia un webhook externo (por ejemplo, un servicio de emails o Slack).
Para el laboratorio lo SIMULAMOS: no hacemos ninguna llamada de red real,
solo registramos el "payload" que se hubiera enviado. Esto es muy útil
para:

  - Correr pruebas end-to-end sin depender de servicios externos.
  - Demostrar que el caso de uso es 100% independiente del transporte
    real usado para notificar (podría ser HTTP, un tópico de Kafka, un
    correo, etc. sin cambiar `CreateOrderUseCase`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.domain.entities import Order


@dataclass
class SentNotification:
    """Registro de una notificación 'enviada' (para poder inspeccionarla en tests)."""

    url: str
    payload: dict
    sent_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SimulatedHttpNotificationAdapter:
    """
    Simula un adaptador HTTP: en vez de llamar a `requests.post`, guarda
    la 'llamada' en `self.sent_notifications` para poder verificarla en
    pruebas de contrato / end-to-end.
    """

    def __init__(
        self, webhook_url: str = "https://notifications.example.com/orders"
    ) -> None:
        self.webhook_url = webhook_url
        self.sent_notifications: list[SentNotification] = []

    def notify_order_created(self, order: Order) -> None:
        payload = {
            "event": "order_created",
            "order_id": order.id,
            "customer_id": order.customer_id,
            "total": str(order.total),
            "status": order.status.value,
        }
        # --- Aquí, en un adaptador real, iría algo como: ---
        # response = requests.post(self.webhook_url, json=payload, timeout=5)
        # response.raise_for_status()
        # ----------------------------------------------------
        self.sent_notifications.append(
            SentNotification(url=self.webhook_url, payload=payload)
        )
