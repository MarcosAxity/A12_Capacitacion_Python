"""Factories / provider pattern: el único lugar del proyecto que conoce
implementaciones CONCRETAS y las conecta entre sí.

Este es el "composition root": todo el resto del código (domain/)
depende solo de Protocols. Aquí, y solo aquí, se decide qué
implementación concreta se usa en tiempo de ejecución. Así se logra
que cambiar de memoria a SQL sea una decisión de configuración, no un
cambio de código en el dominio.
"""

from src.domain.policies import NoDiscount
from src.domain.ports import DiscountPolicy, Notifier, OrderRepository
from src.domain.services import OrderService
from src.infrastructure.memory_repository import InMemoryOrderRepository
from src.infrastructure.notifiers import ConsoleNotifier
from src.infrastructure.sql_repository import SqlOrderRepository


def repository_provider(kind: str = "memory", **kwargs) -> OrderRepository:
    """Provider: entrega una implementación de `OrderRepository` según
    `kind`, sin que el llamador conozca las clases concretas."""
    providers = {
        "memory": lambda: InMemoryOrderRepository(),
        "sql": lambda: SqlOrderRepository(kwargs.get("db_path", ":memory:")),
    }
    try:
        return providers[kind]()
    except KeyError as exc:
        raise ValueError(
            f"Repositorio desconocido '{kind}'. Opciones: {list(providers)}"
        ) from exc


def notifier_provider(kind: str = "console", **kwargs) -> Notifier:
    from src.infrastructure.notifiers import EmailNotifier, SmsNotifier

    providers = {
        "console": lambda: ConsoleNotifier(),
        "email": lambda: EmailNotifier(kwargs.get("smtp_host", "localhost")),
        "sms": lambda: SmsNotifier(kwargs.get("gateway", "twilio-sim")),
    }
    try:
        return providers[kind]()
    except KeyError as exc:
        raise ValueError(
            f"Notifier desconocido '{kind}'. Opciones: {list(providers)}"
        ) from exc


def build_order_service(
    repo_kind: str = "memory",
    notifier_kind: str = "console",
    discount_policy: DiscountPolicy | None = None,
    **kwargs,
) -> OrderService:
    """Composition root: arma un `OrderService` totalmente funcional
    inyectando las implementaciones elegidas. El servicio resultante
    sigue sin conocer nada de sqlite3, print(), etc."""
    repository = repository_provider(repo_kind, **kwargs)
    notifier = notifier_provider(notifier_kind, **kwargs)
    return OrderService(
        repository=repository,
        notifier=notifier,
        discount_policy=discount_policy or NoDiscount(),
    )
