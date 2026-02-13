"""Bot API schemas.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from pydantic import BaseModel, Field

from src.domain.value_objects import BotState


class BotResponse(BaseModel):
    """Bot details response."""

    bot_id: int = Field(..., description="Bot identifier")
    name: str = Field(..., description="Bot name")
    strategy_type: str = Field(..., description="Strategy type")
    state: BotState = Field(..., description="Current bot state")
    capital_allocated: Decimal = Field(..., description="Allocated capital (USDC)")
    current_pnl: Decimal = Field(..., description="Current P&L")
    total_trades: int = Field(..., description="Total trades executed")
    win_rate: Decimal = Field(..., description="Win rate (0-1)")
    sharpe_ratio: Decimal = Field(..., description="Sharpe ratio")
    max_drawdown: Decimal = Field(..., description="Max drawdown (0-1)")
    created_at: datetime = Field(..., description="Bot creation timestamp")
    last_trade_at: datetime | None = Field(None, description="Last trade timestamp")

    class Config:
        from_attributes = True


class BotListResponse(BaseModel):
    """List of bots response."""

    bots: list[BotResponse] = Field(..., description="List of bots")
    total: int = Field(..., description="Total number of bots")


class BotConfigUpdate(BaseModel):
    """Bot configuration update request."""

    config: Dict[str, Any] = Field(..., description="New configuration values")
