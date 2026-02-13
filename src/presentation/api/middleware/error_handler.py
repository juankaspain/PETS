"""Error handler middleware.

Consistent error response format.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import logging
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.domain.exceptions import (
    DomainError,
    InfrastructureError,
    OrderError,
    PETSError,
    RiskViolation,
)

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Handle exceptions with consistent format.
    
    Maps domain exceptions to appropriate HTTP status codes.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Catch and format exceptions."""
        try:
            return await call_next(request)
        except RiskViolation as e:
            logger.warning(
                "risk_violation",
                extra={
                    "error": str(e),
                    "path": request.url.path,
                    "correlation_id": getattr(request.state, "correlation_id", None),
                },
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": str(e),
                    "error_type": "risk_violation",
                },
            )
        except OrderError as e:
            logger.warning(
                "order_error",
                extra={
                    "error": str(e),
                    "path": request.url.path,
                    "correlation_id": getattr(request.state, "correlation_id", None),
                },
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": str(e),
                    "error_type": "order_error",
                },
            )
        except DomainError as e:
            logger.warning(
                "domain_error",
                extra={
                    "error": str(e),
                    "path": request.url.path,
                    "correlation_id": getattr(request.state, "correlation_id", None),
                },
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": str(e),
                    "error_type": "domain_error",
                },
            )
        except InfrastructureError as e:
            logger.error(
                "infrastructure_error",
                extra={
                    "error": str(e),
                    "path": request.url.path,
                    "correlation_id": getattr(request.state, "correlation_id", None),
                },
            )
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "detail": "Service temporarily unavailable",
                    "error_type": "infrastructure_error",
                },
            )
        except PETSError as e:
            logger.error(
                "pets_error",
                extra={
                    "error": str(e),
                    "path": request.url.path,
                    "correlation_id": getattr(request.state, "correlation_id", None),
                },
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal server error",
                    "error_type": "system_error",
                },
            )
        except Exception as e:
            logger.exception(
                "unexpected_error",
                extra={
                    "error": str(e),
                    "path": request.url.path,
                    "correlation_id": getattr(request.state, "correlation_id", None),
                },
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Unexpected error occurred",
                    "error_type": "unknown_error",
                },
            )
