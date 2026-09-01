"""
CONTENEDOR DE INYECCIÓN DE DEPENDENCIAS (wiring).

Este es el único lugar de todo el proyecto donde se decide QUÉ
implementación concreta de cada puerto se va a usar. Todo lo demás
(dominio, aplicación) solo conoce los puertos (interfaces).

Cambiar de repositorio en memoria a SQLAlchemy, o de notificador
simulado a uno real, implica tocar SOLO este archivo.
"""

from __future__ import annotations

from functools import lru_cache

from app.application.use_cases import CreateOrderUseCase, GetOrderUseCase
from app.infrastructure.db.models import Base
from app.infrastructure.notifications.http_notifier import (
    SimulatedHttpNotificationAdapter,
)
from app.infrastructure.persistence.memory_repository import InMemoryOrderRepository
from app.infrastructure.persistence.sqlalchemy_repository import (
    SqlAlchemyOrderRepository,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = "sqlite:///./orders.db"


@lru_cache
def get_engine():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine


@lru_cache
def get_session_factory() -> sessionmaker:
    return sessionmaker(bind=get_engine())


class Container:
    """
    Contenedor simple (sin librerías externas) que construye y comparte
    las instancias de adaptadores y casos de uso usados por la API.

    `use_sqlalchemy=False` -> usa el adaptador en memoria (rápido, sin BD).
    `use_sqlalchemy=True`  -> usa el adaptador SQLAlchemy sobre SQLite.
    """

    def __init__(
        self, use_sqlalchemy: bool = False, session: Session | None = None
    ) -> None:
        self.notifier = SimulatedHttpNotificationAdapter()

        if use_sqlalchemy:
            self.session: Session = session or get_session_factory()()
            self.repository = SqlAlchemyOrderRepository(self.session)
        else:
            self.repository = InMemoryOrderRepository()

        self.create_order_use_case = CreateOrderUseCase(
            repository=self.repository, notifier=self.notifier
        )
        self.get_order_use_case = GetOrderUseCase(repository=self.repository)


# Contenedor por defecto usado por la API (en memoria, para que la demo
# funcione sin configurar nada). Se puede cambiar a SQLAlchemy con la
# variable de entorno USE_SQLALCHEMY=1 (ver app/api/main.py).
