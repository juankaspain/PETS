"""Risk API schemas.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class RiskMetrics(BaseModel):
    """Risk metrics response."""

    bot_id: int | None = Field(None, description="Bot identifier (None for portfolio)")
    current_drawdown: Decimal = Field(..., description="Current drawdown (0-1)")
    max_drawdown: Decimal = Field(..., description="Max drawdown (0-1)")
    consecutive_losses: int = Field(..., description="Consecutive losses count")
    open_exposure: Decimal = Field(..., description="Total open exposure (USDC)")
    daily_loss: Decimal = Field(..., description="Daily loss (USDC)")
    zone_exposures: dict[str, Decimal] = Field(..., description="Exposure by zone")


class CircuitBreakerStatus(BaseModel):
    """Circuit breaker status response."""

    breaker_id: str = Field(..., description="Circuit breaker identifier")
    is_open: bool = Field(..., description="Breaker is open (halted)")
    threshold: Decimal = Field(..., description="Threshold value")
    current_value: Decimal = Field(..., description="Current value")
    triggered_at: datetime | None = Field(None, description="Trigger timestamp")
    auto_reset_at: datetime | None = Field(None, description="Auto reset timestamp")


class EmergencyHaltRequest(BaseModel):
    """Emergency halt request."""

    reason: str = Field(..., description="Halt reason")
    halt_all_bots: bool = Field(True, description="Halt all bots")
    close_positions: bool = Field(False, description="Close all positions")
