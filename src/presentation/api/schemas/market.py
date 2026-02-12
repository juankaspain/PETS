"""Market schemas."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class MarketResponse(BaseModel):
    """Market response."""

    market_id: str
    question: str
    outcomes: list[str]
    liquidity: Decimal
    volume_24h: Decimal | None = None
    yes_price: Decimal | None = None
    no_price: Decimal | None = None
    created_at: datetime
    updated_at: datetime
    resolves_at: datetime | None = None
    resolved: bool = False
    resolved_outcome: str | None = None

    class Config:
        from_attributes = True
