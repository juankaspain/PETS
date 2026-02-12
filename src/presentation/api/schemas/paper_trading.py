"""Paper trading schemas."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PaperTradingStart(BaseModel):
    """Start paper trading request."""

    initial_balance: Decimal = Field(
        Decimal("10000"),
        gt=0,
        description="Initial virtual balance",
    )
    strategy_config: dict = Field(
        default_factory=dict,
        description="Strategy configuration",
    )


class PaperTradingStatus(BaseModel):
    """Paper trading status response."""

    session_id: str
    active: bool
    initial_balance: Decimal
    current_balance: Decimal
    total_value: Decimal
    total_pnl: Decimal
    return_pct: Decimal
    open_positions: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal
    started_at: datetime


class PaperTradeResponse(BaseModel):
    """Paper trade response."""

    position_id: str
    market_id: str
    side: str
    size: Decimal
    entry_price: Decimal
    exit_price: Decimal | None
    realized_pnl: Decimal | None
    opened_at: datetime
    closed_at: datetime | None


class BacktestRequest(BaseModel):
    """Backtest request."""

    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    initial_balance: Decimal = Field(
        Decimal("10000"),
        gt=0,
        description="Initial balance",
    )
    strategy_config: dict = Field(
        default_factory=dict,
        description="Strategy configuration",
    )


class BacktestResponse(BaseModel):
    """Backtest response."""

    backtest_id: str
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_balance: Decimal
    final_balance: Decimal
    total_pnl: Decimal
    return_pct: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal
    profit_factor: Decimal
    sharpe_ratio: Decimal | None
    max_drawdown_pct: Decimal
    trades_count: int
