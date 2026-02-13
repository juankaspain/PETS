"""Order API schemas.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from src.domain.value_objects import OrderStatus, Side, Zone


class PlaceOrderRequest(BaseModel):
    """Place order request."""

    bot_id: int = Field(..., description="Bot placing order")
    market_id: str = Field(..., description="Market identifier")
    side: Side = Field(..., description="Order side (YES/NO)")
    price: Decimal = Field(..., ge=Decimal("0.01"), le=Decimal("0.99"), description="Order price")
    size: Decimal = Field(..., gt=0, description="Order size")
    post_only: bool = Field(True, description="Post-only order (maker)")

    @field_validator("price")
    @classmethod
    def validate_zones(cls, v: Decimal) -> Decimal:
        """Validate price not in prohibited zones."""
        if Decimal("0.60") <= v <= Decimal("0.98"):
            raise ValueError("Zone 4-5 directional trading prohibited")
        return v


class OrderResponse(BaseModel):
    """Order details response."""

    order_id: str = Field(..., description="Order identifier")
    bot_id: int = Field(..., description="Bot identifier")
    market_id: str = Field(..., description="Market identifier")
    side: Side = Field(..., description="Order side")
    price: Decimal = Field(..., description="Order price")
    size: Decimal = Field(..., description="Order size")
    filled_size: Decimal = Field(..., description="Filled size")
    status: OrderStatus = Field(..., description="Order status")
    zone: Zone = Field(..., description="Price zone")
    created_at: datetime = Field(..., description="Order created timestamp")
    filled_at: datetime | None = Field(None, description="Order filled timestamp")

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """List of orders response."""

    orders: list[OrderResponse] = Field(..., description="List of orders")
    total: int = Field(..., description="Total number of orders")
