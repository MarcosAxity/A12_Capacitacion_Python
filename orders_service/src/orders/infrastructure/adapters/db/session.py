"""Fábrica de engine/sesión async de SQLAlchemy."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def make_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    connect_args = {}
    if database_url.startswith("sqlite"):
        # Necesario para permitir el uso del engine desde distintos tasks
        # de asyncio dentro de un mismo proceso (tests, TestClient, etc.)
        connect_args = {"check_same_thread": False}
    return create_async_engine(database_url, echo=echo, connect_args=connect_args)


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
