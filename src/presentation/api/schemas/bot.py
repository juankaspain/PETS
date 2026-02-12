"""Bot schemas."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class BotCreate(BaseModel):
    """Create bot request."""

    strategy_type: str = Field(..., description="Strategy type (e.g., 'VOLATILITY_SKEW')")
    config: dict = Field(..., description="Strategy configuration")
    capital_allocated: Decimal = Field(..., gt=0, description="Capital allocated to bot")


class BotResponse(BaseModel):
    """Bot response."""

    bot_id: int
    strategy_type: str
    state: str
    config: dict
    capital_allocated: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BotStateUpdate(BaseModel):
    """Update bot state request."""

    state: str = Field(
        ...,
        description="New state",
        pattern="^(IDLE|ANALYZING|PLACING|HOLDING|EXITING|STOPPED|ERROR)$",
    )
