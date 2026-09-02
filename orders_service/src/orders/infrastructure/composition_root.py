"""Composition Root: único lugar del proyecto donde se conectan las
implementaciones concretas (adaptadores) con las abstracciones (puertos)
que consume la capa de aplicación. Nada más en el código debería instanciar
adaptadores directamente.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from orders.infrastructure.adapters.db.session import make_engine, make_session_factory
from orders.infrastructure.adapters.events.publishers import LoggingEventPublisher
from orders.infrastructure.config import Settings


@dataclass(slots=True)
class AppContainer:
    """Contenedor de dependencias construido una vez, al arrancar la app."""

    settings: Settings
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    event_publisher: LoggingEventPublisher

    @classmethod
    def build(cls, settings: Settings) -> AppContainer:
        engine = make_engine(settings.database_url, echo=settings.sql_echo)
        session_factory = make_session_factory(engine)
        return cls(
            settings=settings,
            engine=engine,
            session_factory=session_factory,
            event_publisher=LoggingEventPublisher(),
        )

    async def dispose(self) -> None:
        await self.engine.dispose()
