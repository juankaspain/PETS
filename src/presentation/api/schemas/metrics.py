"""Metrics API schemas.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from decimal import Decimal

from pydantic import BaseModel, Field


class BotMetrics(BaseModel):
    """Bot performance metrics."""

    bot_id: int = Field(..., description="Bot identifier")
    total_trades: int = Field(..., description="Total trades")
    win_rate: Decimal = Field(..., description="Win rate (0-1)")
    avg_profit: Decimal = Field(..., description="Average profit per trade")
    total_pnl: Decimal = Field(..., description="Total P&L")
    sharpe_ratio: Decimal = Field(..., description="Sharpe ratio")
    max_drawdown: Decimal = Field(..., description="Max drawdown (0-1)")
    avg_hold_time_hours: Decimal = Field(..., description="Average hold time (hours)")
    fill_rate: Decimal = Field(..., description="Order fill rate (0-1)")
    avg_slippage: Decimal = Field(..., description="Average slippage")


class PortfolioMetrics(BaseModel):
    """Portfolio-wide metrics."""

    total_capital: Decimal = Field(..., description="Total capital")
    total_pnl: Decimal = Field(..., description="Total P&L")
    roi: Decimal = Field(..., description="Return on investment")
    active_bots: int = Field(..., description="Number of active bots")
    open_positions: int = Field(..., description="Number of open positions")
    total_trades_today: int = Field(..., description="Trades today")
    portfolio_sharpe: Decimal = Field(..., description="Portfolio Sharpe ratio")
    portfolio_drawdown: Decimal = Field(..., description="Current drawdown")


class PrometheusMetrics(BaseModel):
    """Prometheus format metrics."""

    metrics: str = Field(..., description="Metrics in Prometheus format")
