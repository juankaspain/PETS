"""Backtest metrics calculator."""

import logging
from decimal import Decimal
from typing import List

import numpy as np

from src.infrastructure.paper_trading.paper_wallet import PaperPosition

logger = logging.getLogger(__name__)


class BacktestMetrics:
    """Calculates performance metrics for backtesting.

    Computes:
    - Win rate, profit factor
    - Sharpe ratio, Sortino ratio
    - Max drawdown, current drawdown
    - Average win/loss
    - Risk-adjusted returns
    """

    @staticmethod
    def calculate_win_rate(positions: List[PaperPosition]) -> Decimal:
        """Calculate win rate.

        Args:
            positions: List of closed positions

        Returns:
            Win rate (0.0 to 1.0)
        """
        if not positions:
            return Decimal("0")

        winning = sum(
            1 for p in positions if p.realized_pnl and p.realized_pnl > 0
        )
        return Decimal(winning) / Decimal(len(positions))

    @staticmethod
    def calculate_profit_factor(positions: List[PaperPosition]) -> Decimal:
        """Calculate profit factor.

        Args:
            positions: List of closed positions

        Returns:
            Profit factor (gross profit / gross loss)
        """
        gross_profit = sum(
            p.realized_pnl
            for p in positions
            if p.realized_pnl and p.realized_pnl > 0
        )
        gross_loss = sum(
            abs(p.realized_pnl)
            for p in positions
            if p.realized_pnl and p.realized_pnl < 0
        )

        if gross_loss == 0:
            return Decimal("0") if gross_profit == 0 else Decimal("999")

        return gross_profit / gross_loss

    @staticmethod
    def calculate_sharpe_ratio(
        returns: List[Decimal],
        risk_free_rate: Decimal = Decimal("0.05"),
    ) -> Decimal:
        """Calculate Sharpe ratio.

        Args:
            returns: List of returns (e.g., daily returns)
            risk_free_rate: Annual risk-free rate

        Returns:
            Sharpe ratio
        """
        if len(returns) < 2:
            return Decimal("0")

        returns_array = np.array([float(r) for r in returns])
        mean_return = Decimal(str(np.mean(returns_array)))
        std_return = Decimal(str(np.std(returns_array)))

        if std_return == 0:
            return Decimal("0")

        # Annualized Sharpe
        excess_return = mean_return - risk_free_rate / Decimal("252")  # Daily
        sharpe = excess_return / std_return * Decimal(str(np.sqrt(252)))

        return sharpe

    @staticmethod
    def calculate_max_drawdown(equity_curve: List[Decimal]) -> Decimal:
        """Calculate maximum drawdown.

        Args:
            equity_curve: List of portfolio values over time

        Returns:
            Max drawdown as percentage
        """
        if len(equity_curve) < 2:
            return Decimal("0")

        equity_array = np.array([float(e) for e in equity_curve])
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max
        max_dd = abs(float(np.min(drawdown)))

        return Decimal(str(max_dd * 100))  # Return as percentage

    @staticmethod
    def calculate_sortino_ratio(
        returns: List[Decimal],
        risk_free_rate: Decimal = Decimal("0.05"),
    ) -> Decimal:
        """Calculate Sortino ratio.

        Args:
            returns: List of returns
            risk_free_rate: Annual risk-free rate

        Returns:
            Sortino ratio
        """
        if len(returns) < 2:
            return Decimal("0")

        returns_array = np.array([float(r) for r in returns])
        mean_return = Decimal(str(np.mean(returns_array)))

        # Downside deviation (only negative returns)
        negative_returns = returns_array[returns_array < 0]
        if len(negative_returns) == 0:
            return Decimal("999")  # No downside risk

        downside_std = Decimal(str(np.std(negative_returns)))

        if downside_std == 0:
            return Decimal("0")

        # Annualized Sortino
        excess_return = mean_return - risk_free_rate / Decimal("252")
        sortino = excess_return / downside_std * Decimal(str(np.sqrt(252)))

        return sortino
