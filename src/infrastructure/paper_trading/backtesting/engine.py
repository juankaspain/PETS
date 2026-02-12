"""Backtesting engine for strategy validation."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List

from src.application.bots.bot8_volatility_skew import Bot8VolatilitySkew
from src.infrastructure.paper_trading.paper_wallet import PaperWallet
from src.infrastructure.paper_trading.market_simulator import MarketSimulator

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Backtest result."""

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


class BacktestEngine:
    """Engine for backtesting trading strategies on historical data.

    Replays historical market data through strategy.
    Simulates trades with paper wallet.
    Calculates performance metrics.
    """

    def __init__(
        self,
        strategy: Bot8VolatilitySkew,
        initial_balance: Decimal = Decimal("10000"),
    ):
        """Initialize backtest engine.

        Args:
            strategy: Trading strategy to test
            initial_balance: Starting balance
        """
        self.strategy = strategy
        self.wallet = PaperWallet(initial_balance)
        self.market_simulator = MarketSimulator()

        logger.info(
            "Backtest engine initialized",
            extra={
                "strategy": strategy.__class__.__name__,
                "initial_balance": float(initial_balance),
            },
        )

    def run(
        self,
        market_id: str,
        start_date: datetime,
        end_date: datetime,
        price_data: List[tuple[datetime, Decimal]],
    ) -> BacktestResult:
        """Run backtest on historical data.

        Args:
            market_id: Market ID
            start_date: Start date
            end_date: End date
            price_data: List of (timestamp, price) tuples

        Returns:
            Backtest result
        """
        logger.info(
            "Starting backtest",
            extra={
                "market_id": market_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "data_points": len(price_data),
            },
        )

        # Add market to simulator
        if price_data:
            initial_price = price_data[0][1]
            self.market_simulator.add_market(
                market_id=market_id,
                initial_yes_price=initial_price,
                initial_no_price=Decimal("1.0") - initial_price,
            )

        # Replay price data
        for timestamp, price in price_data:
            # Update market price
            self.market_simulator.update_price(market_id, price)
            snapshot = self.market_simulator.get_snapshot(market_id)

            # Check if strategy wants to enter
            if not self.wallet.open_positions:
                should_enter, entry_side = self.strategy.analyze_market(
                    market_id=market_id,
                    yes_price=float(snapshot.yes_price),
                    no_price=float(snapshot.no_price),
                    liquidity=float(snapshot.liquidity),
                )

                if should_enter:
                    # Calculate position size (simplified)
                    position_size = self.wallet.balance * Decimal("0.15")  # 15% max

                    # Open position
                    try:
                        self.wallet.open_position(
                            market_id=market_id,
                            side=entry_side,
                            size=position_size,
                            price=snapshot.yes_price
                            if entry_side == "BUY"
                            else snapshot.no_price,
                        )
                        logger.info(
                            "Position opened in backtest",
                            extra={
                                "timestamp": timestamp.isoformat(),
                                "side": entry_side,
                                "price": float(snapshot.yes_price),
                            },
                        )
                    except ValueError as e:
                        logger.warning(f"Failed to open position: {e}")

            # Check if strategy wants to exit
            for position in self.wallet.open_positions:
                should_exit = self.strategy.should_exit(
                    position_id=str(position.position_id),
                    entry_price=float(position.entry_price),
                    current_price=float(snapshot.yes_price),
                    holding_hours=(
                        (timestamp - position.opened_at).total_seconds() / 3600
                    ),
                )

                if should_exit:
                    # Close position
                    self.wallet.close_position(
                        position_id=position.position_id,
                        exit_price=snapshot.yes_price,
                    )
                    logger.info(
                        "Position closed in backtest",
                        extra={
                            "timestamp": timestamp.isoformat(),
                            "entry": float(position.entry_price),
                            "exit": float(snapshot.yes_price),
                        },
                    )

        # Calculate metrics
        stats = self.wallet.get_statistics()
        closed = self.wallet.closed_positions

        winning_trades = [
            p for p in closed if p.realized_pnl and p.realized_pnl > 0
        ]
        losing_trades = [
            p for p in closed if p.realized_pnl and p.realized_pnl < 0
        ]

        avg_win = (
            sum(p.realized_pnl for p in winning_trades) / len(winning_trades)
            if winning_trades
            else Decimal("0")
        )
        avg_loss = (
            sum(abs(p.realized_pnl) for p in losing_trades) / len(losing_trades)
            if losing_trades
            else Decimal("0")
        )
        profit_factor = avg_win / avg_loss if avg_loss > 0 else Decimal("0")

        result = BacktestResult(
            start_date=start_date,
            end_date=end_date,
            initial_balance=self.wallet.initial_balance,
            final_balance=self.wallet.total_value,
            total_return=self.wallet.total_pnl,
            total_return_pct=Decimal(str(stats["return_pct"])),
            total_trades=len(closed),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=Decimal(str(stats["win_rate"])),
            profit_factor=profit_factor,
            sharpe_ratio=None,  # TODO: Calculate
            max_drawdown=Decimal("0"),  # TODO: Calculate
            avg_win=avg_win,
            avg_loss=avg_loss,
        )

        logger.info(
            "Backtest completed",
            extra={
                "total_trades": result.total_trades,
                "win_rate": float(result.win_rate),
                "total_return_pct": float(result.total_return_pct),
                "profit_factor": float(result.profit_factor),
            },
        )

        return result
