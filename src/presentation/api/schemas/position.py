"""Position schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PositionResponse(BaseModel):
    """Position response."""

    position_id: UUID
    bot_id: int
    order_id: UUID
    market_id: str
    side: str
    size: Decimal
    entry_price: Decimal
    zone: int
    opened_at: datetime
    current_price: Decimal | None = None
    realized_pnl: Decimal | None = None
    unrealized_pnl: Decimal | None = None
    closed_at: datetime | None = None

    class Config:
        from_attributes = True


class PositionClose(BaseModel):
    """Close position request."""

    exit_price: Decimal = Field(
        ..., ge=0.01, le=0.99, description="Exit price (0.01 to 0.99)"
    )
    reason: str | None = Field(None, description="Close reason")
