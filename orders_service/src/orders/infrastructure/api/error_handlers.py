"""Traduce excepciones de dominio a respuestas HTTP.

Este es el único punto del sistema que conoce simultáneamente las
excepciones del dominio y los códigos de estado HTTP: mantiene al dominio
libre de dependencias de FastAPI.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from orders.domain.exceptions import (
    EmptyOrderError,
    InvalidItemQuantityError,
    InvalidOrderStateError,
    OrderNotFoundError,
)
from orders.infrastructure.api.schemas import ErrorResponse

_STATUS_BY_EXCEPTION: list[tuple[type[Exception], int]] = [
    (OrderNotFoundError, status.HTTP_404_NOT_FOUND),
    (EmptyOrderError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (InvalidOrderStateError, status.HTTP_409_CONFLICT),
    (InvalidItemQuantityError, status.HTTP_422_UNPROCESSABLE_CONTENT),
]


def register_error_handlers(app: FastAPI) -> None:
    for exc_type, http_status in _STATUS_BY_EXCEPTION:

        def _make_handler(
            status_code: int,
        ) -> Callable[[Request, Exception], Awaitable[JSONResponse]]:
            async def _handler(request: Request, exc: Exception) -> JSONResponse:
                return JSONResponse(
                    status_code=status_code,
                    content=ErrorResponse(
                        detail=str(exc), error_type=type(exc).__name__
                    ).model_dump(),
                )

            return _handler

        app.add_exception_handler(exc_type, _make_handler(http_status))
