"""Position API schemas.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from src.domain.value_objects import Side, Zone


class PositionResponse(BaseModel):
    """Position details response."""

    position_id: str = Field(..., description="Position identifier")
    bot_id: int = Field(..., description="Bot identifier")
    market_id: str = Field(..., description="Market identifier")
    side: Side = Field(..., description="Position side (YES/NO)")
    entry_price: Decimal = Field(..., description="Entry price")
    current_price: Decimal = Field(..., description="Current price")
    size: Decimal = Field(..., description="Position size")
    unrealized_pnl: Decimal = Field(..., description="Unrealized P&L")
    zone: Zone = Field(..., description="Price zone")
    opened_at: datetime = Field(..., description="Position opened timestamp")
    closed_at: datetime | None = Field(None, description="Position closed timestamp")

    class Config:
        from_attributes = True


class PositionListResponse(BaseModel):
    """List of positions response."""

    positions: list[PositionResponse] = Field(..., description="List of positions")
    total: int = Field(..., description="Total number of positions")


class ClosePositionRequest(BaseModel):
    """Close position request."""

    reason: str | None = Field(None, description="Close reason")
