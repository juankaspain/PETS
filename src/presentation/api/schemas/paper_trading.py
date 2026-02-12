"""Paper trading schemas."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PaperTradingStartRequest(BaseModel):
    """Start paper trading request."""

    initial_balance: Decimal = Field(
        Decimal("10000"), gt=0, description="Initial balance"
    )
    bot_config: dict | None = Field(None, description="Bot configuration")


class PaperTradingStatusResponse(BaseModel):
    """Paper trading status response."""

    session_id: str
    is_running: bool
    started_at: datetime
    initial_balance: Decimal
    current_balance: Decimal
    total_value: Decimal
    total_pnl: Decimal
    open_positions: int
    closed_positions: int
    total_trades: int
    win_rate: Decimal


class WalletStateResponse(BaseModel):
    """Wallet state response."""

    balance: Decimal
    total_value: Decimal
    total_pnl: Decimal
    open_positions: list[dict]
    closed_positions: list[dict]


class BacktestRequest(BaseModel):
    """Backtest request."""

    market_id: str = Field(..., description="Market ID")
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    initial_balance: Decimal = Field(
        Decimal("10000"), gt=0, description="Initial balance"
    )
    bot_config: dict | None = Field(None, description="Bot configuration")


class BacktestResponse(BaseModel):
    """Backtest response."""

    start_date: datetime
    end_date: datetime
    initial_balance: Decimal
    final_balance: Decimal
    total_return: Decimal
    total_return_pct: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal
    profit_factor: Decimal
    sharpe_ratio: Decimal | None
    max_drawdown: Decimal
    avg_win: Decimal
    avg_loss: Decimal

    class Config:
        from_attributes = True
