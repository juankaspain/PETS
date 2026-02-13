"""Health check API schemas.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness health check response."""

    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="Check timestamp")


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    status: str = Field(..., description="Readiness status")
    database: bool = Field(..., description="Database connectivity")
    redis: bool = Field(..., description="Redis connectivity")
    websocket: bool = Field(..., description="WebSocket connectivity")


class StartupResponse(BaseModel):
    """Startup check response."""

    status: str = Field(..., description="Startup status")
    migrations_applied: bool = Field(..., description="DB migrations status")
    bots_initialized: int = Field(..., description="Number of bots initialized")
