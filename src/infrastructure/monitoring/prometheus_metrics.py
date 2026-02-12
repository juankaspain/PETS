"""Prometheus metrics exporter."""

import logging
from decimal import Decimal

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# Portfolio metrics
portfolio_value = Gauge(
    "pets_portfolio_value_usdc",
    "Current portfolio value in USDC",
)

open_positions_count = Gauge(
    "pets_open_positions_count",
    "Number of open positions",
    ["bot_id"],
)

realized_pnl = Gauge(
    "pets_realized_pnl_usdc",
    "Realized P&L in USDC",
    ["bot_id"],
)

unrealized_pnl = Gauge(
    "pets_unrealized_pnl_usdc",
    "Unrealized P&L in USDC",
    ["bot_id"],
)

# Circuit breaker metrics
circuit_breaker_status = Gauge(
    "pets_circuit_breaker_status",
    "Circuit breaker status (1=active, 0=inactive)",
    ["bot_id"],
)

consecutive_losses = Gauge(
    "pets_consecutive_losses",
    "Consecutive losses count",
    ["bot_id"],
)

drawdown_pct = Gauge(
    "pets_drawdown_pct",
    "Drawdown percentage",
    ["type"],  # bot or portfolio
)

# Trading metrics
trades_total = Counter(
    "pets_trades_total",
    "Total number of trades",
    ["bot_id", "result"],  # result: win or loss
)

win_rate = Gauge(
    "pets_win_rate_pct",
    "Win rate percentage",
    ["bot_id"],
)

profit_factor = Gauge(
    "pets_profit_factor",
    "Profit factor (wins/losses)",
    ["bot_id"],
)

# Bot health metrics
bot_health = Gauge(
    "pets_bot_health",
    "Bot health status (1=healthy, 0=unhealthy)",
    ["bot_id"],
)

bot_uptime_seconds = Gauge(
    "pets_bot_uptime_seconds",
    "Bot uptime in seconds",
    ["bot_id"],
)

# Transaction metrics
transaction_gas_used = Histogram(
    "pets_transaction_gas_used",
    "Gas used per transaction",
    buckets=[100000, 200000, 300000, 500000, 1000000],
)

transaction_cost_matic = Histogram(
    "pets_transaction_cost_matic",
    "Transaction cost in MATIC",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
)

# API metrics
api_requests_total = Counter(
    "pets_api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"],
)

api_request_duration_seconds = Histogram(
    "pets_api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"],
)


class MetricsExporter:
    """Prometheus metrics exporter."""

    @staticmethod
    def update_portfolio_value(value: Decimal) -> None:
        """Update portfolio value metric.

        Args:
            value: Portfolio value
        """
        portfolio_value.set(float(value))

    @staticmethod
    def update_open_positions(bot_id: int, count: int) -> None:
        """Update open positions count.

        Args:
            bot_id: Bot ID
            count: Position count
        """
        open_positions_count.labels(bot_id=bot_id).set(count)

    @staticmethod
    def update_pnl(bot_id: int, realized: Decimal, unrealized: Decimal) -> None:
        """Update P&L metrics.

        Args:
            bot_id: Bot ID
            realized: Realized P&L
            unrealized: Unrealized P&L
        """
        realized_pnl.labels(bot_id=bot_id).set(float(realized))
        unrealized_pnl.labels(bot_id=bot_id).set(float(unrealized))

    @staticmethod
    def update_circuit_breaker(
        bot_id: int,
        is_active: bool,
        consecutive: int,
    ) -> None:
        """Update circuit breaker metrics.

        Args:
            bot_id: Bot ID
            is_active: Circuit breaker active
            consecutive: Consecutive losses
        """
        circuit_breaker_status.labels(bot_id=bot_id).set(1 if is_active else 0)
        consecutive_losses.labels(bot_id=bot_id).set(consecutive)

    @staticmethod
    def update_drawdown(drawdown_type: str, pct: Decimal) -> None:
        """Update drawdown metric.

        Args:
            drawdown_type: 'bot' or 'portfolio'
            pct: Drawdown percentage
        """
        drawdown_pct.labels(type=drawdown_type).set(float(pct))

    @staticmethod
    def record_trade(bot_id: int, is_win: bool) -> None:
        """Record trade result.

        Args:
            bot_id: Bot ID
            is_win: Trade was profitable
        """
        result = "win" if is_win else "loss"
        trades_total.labels(bot_id=bot_id, result=result).inc()

    @staticmethod
    def update_win_rate(bot_id: int, rate: Decimal) -> None:
        """Update win rate.

        Args:
            bot_id: Bot ID
            rate: Win rate percentage
        """
        win_rate.labels(bot_id=bot_id).set(float(rate))

    @staticmethod
    def update_profit_factor(bot_id: int, factor: Decimal) -> None:
        """Update profit factor.

        Args:
            bot_id: Bot ID
            factor: Profit factor
        """
        profit_factor.labels(bot_id=bot_id).set(float(factor))

    @staticmethod
    def update_bot_health(bot_id: int, is_healthy: bool) -> None:
        """Update bot health.

        Args:
            bot_id: Bot ID
            is_healthy: Bot is healthy
        """
        bot_health.labels(bot_id=bot_id).set(1 if is_healthy else 0)

    @staticmethod
    def record_transaction_gas(gas_used: int, cost_matic: Decimal) -> None:
        """Record transaction gas metrics.

        Args:
            gas_used: Gas units used
            cost_matic: Cost in MATIC
        """
        transaction_gas_used.observe(gas_used)
        transaction_cost_matic.observe(float(cost_matic))
