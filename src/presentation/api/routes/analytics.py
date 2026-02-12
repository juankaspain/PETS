"""Analytics routes."""

import logging
from decimal import Decimal

from fastapi import APIRouter

from src.presentation.api.dependencies import TimescaleDB
from src.presentation.api.schemas.analytics import (
    PerformanceMetrics,
    PortfolioMetrics,
    RiskMetrics,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/portfolio", response_model=PortfolioMetrics)
async def get_portfolio_metrics(
    db: TimescaleDB,
):
    """Get portfolio metrics.

    Args:
        db: TimescaleDB client

    Returns:
        Portfolio metrics
    """
    # Simplified queries - real implementation would use continuous aggregates

    # Total value (mock)
    total_value = Decimal("10000")
    cash_balance = Decimal("5000")
    position_value = Decimal("5000")

    # P&L queries
    daily_pnl_query = """
        SELECT COALESCE(SUM(realized_pnl), 0) as daily_pnl
        FROM positions
        WHERE closed_at >= NOW() - INTERVAL '24 hours'
    """
    daily_pnl_row = await db.pool.fetchrow(daily_pnl_query)
    daily_pnl = daily_pnl_row["daily_pnl"] or Decimal("0")

    total_pnl_query = """
        SELECT COALESCE(SUM(realized_pnl), 0) as total_pnl
        FROM positions
        WHERE closed_at IS NOT NULL
    """
    total_pnl_row = await db.pool.fetchrow(total_pnl_query)
    total_pnl = total_pnl_row["total_pnl"] or Decimal("0")

    # Positions count
    positions_query = "SELECT COUNT(*) FROM positions WHERE closed_at IS NULL"
    open_positions = await db.pool.fetchval(positions_query)

    # Active bots
    bots_query = "SELECT COUNT(*) FROM bots WHERE state NOT IN ('STOPPED', 'ERROR')"
    active_bots = await db.pool.fetchval(bots_query)

    return PortfolioMetrics(
        total_value=total_value,
        cash_balance=cash_balance,
        position_value=position_value,
        daily_pnl=daily_pnl,
        total_pnl=total_pnl,
        daily_return_pct=daily_pnl / total_value * Decimal("100")
        if total_value > 0
        else Decimal("0"),
        total_return_pct=total_pnl / total_value * Decimal("100")
        if total_value > 0
        else Decimal("0"),
        open_positions=open_positions or 0,
        active_bots=active_bots or 0,
    )


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    db: TimescaleDB,
):
    """Get performance metrics.

    Args:
        db: TimescaleDB client

    Returns:
        Performance metrics
    """
    # Trade stats
    trades_query = """
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE realized_pnl > 0) as wins,
            COUNT(*) FILTER (WHERE realized_pnl < 0) as losses,
            AVG(realized_pnl) FILTER (WHERE realized_pnl > 0) as avg_win,
            AVG(ABS(realized_pnl)) FILTER (WHERE realized_pnl < 0) as avg_loss
        FROM positions
        WHERE closed_at IS NOT NULL
    """

    row = await db.pool.fetchrow(trades_query)

    total_trades = row["total"] or 0
    winning_trades = row["wins"] or 0
    losing_trades = row["losses"] or 0
    avg_win = row["avg_win"] or Decimal("0")
    avg_loss = row["avg_loss"] or Decimal("0")

    win_rate = (
        Decimal(winning_trades) / Decimal(total_trades)
        if total_trades > 0
        else Decimal("0")
    )

    profit_factor = avg_win / avg_loss if avg_loss > 0 else Decimal("0")

    return PerformanceMetrics(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=win_rate,
        avg_win=avg_win,
        avg_loss=avg_loss,
        profit_factor=profit_factor,
        sharpe_ratio=None,  # TODO: Calculate
        max_drawdown_pct=Decimal("0"),  # TODO: Calculate
        current_drawdown_pct=Decimal("0"),  # TODO: Calculate
    )


@router.get("/risk", response_model=RiskMetrics)
async def get_risk_metrics(
    db: TimescaleDB,
):
    """Get risk metrics.

    Args:
        db: TimescaleDB client

    Returns:
        Risk metrics
    """
    # Zone exposure
    zone_query = """
        SELECT
            zone,
            SUM(size * entry_price) as exposure
        FROM positions
        WHERE closed_at IS NULL
        GROUP BY zone
    """

    zone_rows = await db.pool.fetch(zone_query)
    zone_exposure = {f"Z{row['zone']}": row["exposure"] for row in zone_rows}

    return RiskMetrics(
        var_95=Decimal("500"),  # TODO: Calculate
        var_99=Decimal("1000"),  # TODO: Calculate
        max_position_size_pct=Decimal("15"),
        current_leverage=Decimal("1.0"),
        circuit_breaker_status={
            "consecutive_losses": 0,
            "daily_loss_triggered": False,
            "bot_drawdown_triggered": False,
            "portfolio_drawdown_triggered": False,
        },
        zone_exposure=zone_exposure,
        position_concentration=Decimal("0"),  # TODO: Calculate
    )
