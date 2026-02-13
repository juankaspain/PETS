"""Request ID middleware.

Generates correlation_id for distributed tracing.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add correlation ID to each request.
    
    Generates UUID4 for tracing across services.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Generate and attach correlation ID."""
        # Check if correlation_id already exists
        correlation_id = request.headers.get("X-Correlation-ID")
        
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Store in request state
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response
