"""Health check routes.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from datetime import datetime

from fastapi import APIRouter, Depends

from src.presentation.api.dependencies import (
    get_health_checker,
)
from src.presentation.api.schemas import (
    HealthResponse,
    ReadinessResponse,
    StartupResponse,
)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    """Liveness check.
    
    Returns:
        Always returns 200 if service is alive
    """
    return HealthResponse(
        status="alive",
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness(
    health_checker=Depends(get_health_checker),
) -> ReadinessResponse:
    """Readiness check.
    
    Returns:
        200 if service is ready to accept requests
        503 if dependencies unavailable
    """
    checks = await health_checker.check_readiness()
    return ReadinessResponse(
        status="ready" if all(checks.values()) else "not_ready",
        database=checks.get("database", False),
        redis=checks.get("redis", False),
        websocket=checks.get("websocket", False),
    )


@router.get("/startup", response_model=StartupResponse)
async def startup(
    health_checker=Depends(get_health_checker),
) -> StartupResponse:
    """Startup check.
    
    Returns:
        200 if service initialization complete
        503 if still starting up
    """
    status_info = await health_checker.check_startup()
    return StartupResponse(
        status="ready" if status_info.get("ready") else "starting",
        migrations_applied=status_info.get("migrations_applied", False),
        bots_initialized=status_info.get("bots_initialized", 0),
    )
