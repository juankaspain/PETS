"""Backtest strategy use case."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List

from src.application.bots.bot8_volatility_skew import Bot8VolatilitySkew
from src.infrastructure.paper_trading.backtest_engine import (
    BacktestEngine,
    BacktestResult,
)

logger = logging.getLogger(__name__)


class BacktestStrategyUseCase:
    """Use case for backtesting trading strategy."""

    def __init__(self):
        """Initialize use case."""
        pass

    async def execute(
        self,
        strategy_config: Dict,
        historical_data: List[Dict],
        start_date: datetime,
        end_date: datetime,
        initial_balance: Decimal = Decimal("10000"),
    ) -> BacktestResult:
        """Execute backtest.

        Args:
            strategy_config: Strategy configuration
            historical_data: Historical market data
            start_date: Backtest start date
            end_date: Backtest end date
            initial_balance: Starting balance

        Returns:
            Backtest result with performance metrics
        """
        logger.info(
            "Starting backtest use case",
            extra={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "initial_balance": float(initial_balance),
            },
        )

        # Create strategy instance
        strategy = Bot8VolatilitySkew(config=strategy_config)

        # Create backtest engine
        engine = BacktestEngine(initial_balance=initial_balance)

        # Run backtest
        result = engine.run_backtest(
            strategy=strategy,
            historical_data=historical_data,
            start_date=start_date,
            end_date=end_date,
        )

        logger.info(
            "Backtest completed",
            extra={
                "total_pnl": float(result.total_pnl),
                "return_pct": float(result.return_pct),
                "win_rate": float(result.win_rate),
                "total_trades": result.total_trades,
            },
        )

        return result
