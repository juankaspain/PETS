"""Authentication middleware.

Validates API key from X-API-Key header.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import logging
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authenticate requests via API key.
    
    Validates X-API-Key header against configured key.
    Excludes health endpoints from authentication.
    """

    def __init__(self, app, api_key: str) -> None:
        super().__init__(app)
        self.api_key = api_key
        self.excluded_paths = ["/health", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate API key for protected endpoints."""
        # Skip auth for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # Validate API key
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != self.api_key:
            logger.warning(
                "auth_failed",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "client": request.client.host if request.client else None,
                },
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or missing API key"},
            )

        return await call_next(request)
