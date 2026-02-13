"""Rate limiting middleware.

Redis-backed rate limiter: 100 requests/minute per client.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import logging
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limit requests per client IP.
    
    Uses Redis sliding window: 100 requests/minute.
    """

    def __init__(self, app, redis: Redis, limit: int = 100, window: int = 60) -> None:
        super().__init__(app)
        self.redis = redis
        self.limit = limit
        self.window = window

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit before processing request."""
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}"

        # Increment counter
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.window)
        result = await pipe.execute()
        
        current = result[0]

        # Check limit
        if current > self.limit:
            logger.warning(
                "rate_limit_exceeded",
                extra={
                    "client_ip": client_ip,
                    "requests": current,
                    "limit": self.limit,
                    "path": request.url.path,
                },
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded: {self.limit} requests per {self.window}s"
                },
                headers={
                    "X-RateLimit-Limit": str(self.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(self.window),
                },
            )

        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(self.limit - current)
        response.headers["X-RateLimit-Reset"] = str(self.window)

        return response
