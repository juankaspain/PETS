"""Logging middleware.

JSON structured logging for all requests/responses.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests and responses.
    
    Includes: method, path, status, duration, correlation_id.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request/response with timing."""
        start_time = time.time()

        # Get correlation_id from state
        correlation_id = getattr(request.state, "correlation_id", None)

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log request/response
        logger.info(
            "http_request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "correlation_id": correlation_id,
                "client_ip": request.client.host if request.client else None,
            },
        )

        return response
