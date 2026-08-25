import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("lab_api")
logging.basicConfig(level=logging.INFO)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware simple que mide el tiempo de respuesta y loggea cada request."""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        response.headers["X-Process-Time-ms"] = f"{duration_ms:.2f}"
        logger.info(
            "%s %s -> %s (%.2f ms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
