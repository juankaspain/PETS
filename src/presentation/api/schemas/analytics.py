"""Analytics schemas."""

from decimal import Decimal

from pydantic import BaseModel


class PortfolioMetrics(BaseModel):
    """Portfolio metrics response."""

    total_value: Decimal
    cash_balance: Decimal
    position_value: Decimal
    daily_pnl: Decimal
    total_pnl: Decimal
    daily_return_pct: Decimal
    total_return_pct: Decimal
    open_positions: int
    active_bots: int


class PerformanceMetrics(BaseModel):
    """Performance metrics response."""

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    profit_factor: Decimal
    sharpe_ratio: Decimal | None = None
    max_drawdown_pct: Decimal
    current_drawdown_pct: Decimal


class RiskMetrics(BaseModel):
    """Risk metrics response."""

    var_95: Decimal
    var_99: Decimal
    max_position_size_pct: Decimal
    current_leverage: Decimal
    circuit_breaker_status: dict
    zone_exposure: dict[str, Decimal]
    position_concentration: Decimal
