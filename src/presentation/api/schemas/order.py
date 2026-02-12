"""Order schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    """Create order request."""

    bot_id: int = Field(..., description="Bot ID")
    market_id: str = Field(..., description="Market ID")
    side: str = Field(..., description="Order side (BUY or SELL)", pattern="^(BUY|SELL)$")
    size: Decimal = Field(..., gt=0, description="Order size")
    price: Decimal = Field(
        ..., ge=0.01, le=0.99, description="Limit price (0.01 to 0.99)"
    )
    zone: int = Field(..., ge=1, le=5, description="Risk zone (1-5)")
    post_only: bool = Field(True, description="Post-only flag (default True)")


class OrderResponse(BaseModel):
    """Order response."""

    order_id: UUID
    bot_id: int
    market_id: str
    side: str
    size: Decimal
    price: Decimal
    zone: int
    status: str
    post_only: bool
    created_at: datetime
    updated_at: datetime
    filled_size: Decimal | None = None

    class Config:
        from_attributes = True


class OrderCancel(BaseModel):
    """Cancel order request."""

    reason: str | None = Field(None, description="Cancellation reason")
