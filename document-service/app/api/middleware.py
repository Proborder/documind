import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.core.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        clear_contextvars()
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        bind_contextvars(request_id=request_id)
        logger.info("request_started", path=request.url.path, method=request.method)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info("request_finished", status_code=response.status_code)

        return response
