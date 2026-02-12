"""Backtesting engine for historical strategy validation."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List

from src.application.bots.bot8_volatility_skew import Bot8VolatilitySkew
from src.domain.entities.bot import Bot, BotState
from src.domain.entities.market import Market
from src.domain.value_objects.price import Price
from src.infrastructure.paper_trading.paper_wallet import PaperWallet
from src.infrastructure.paper_trading.simulated_execution import SimulatedExecution

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Backtest result."""

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
    trades: List[dict]

    def to_dict(self) -> dict:
        """Convert to dict."""
        return {
            "strategy_name": self.strategy_name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "initial_balance": float(self.initial_balance),
            "final_balance": float(self.final_balance),
            "total_pnl": float(self.total_pnl),
            "return_pct": float(self.return_pct),
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": float(self.win_rate),
            "profit_factor": float(self.profit_factor),
            "sharpe_ratio": float(self.sharpe_ratio) if self.sharpe_ratio else None,
            "max_drawdown_pct": float(self.max_drawdown_pct),
            "trades_count": len(self.trades),
        }


class BacktestEngine:
    """Backtest engine for historical strategy validation.

    Replays historical market data and executes strategy in paper wallet.
    """

    def __init__(self, initial_balance: Decimal = Decimal("10000")):
        """Initialize backtest engine.

        Args:
            initial_balance: Starting balance (default $10K)
        """
        self.initial_balance = initial_balance

    def run_backtest(
        self,
        strategy: Bot8VolatilitySkew,
        historical_data: List[Dict],
        start_date: datetime,
        end_date: datetime,
    ) -> BacktestResult:
        """Run backtest on historical data.

        Args:
            strategy: Trading strategy instance
            historical_data: List of market snapshots with timestamps
            start_date: Backtest start date
            end_date: Backtest end date

        Returns:
            Backtest result with performance metrics
        """
        logger.info(
            "Starting backtest",
            extra={
                "strategy": strategy.__class__.__name__,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "initial_balance": float(self.initial_balance),
            },
        )

        # Initialize paper trading
        paper_wallet = PaperWallet(self.initial_balance)
        execution_engine = SimulatedExecution(paper_wallet)

        # Create mock bot entity
        bot = Bot(
            bot_id=1,
            strategy_type="VOLATILITY_SKEW",
            state=BotState.ANALYZING,
            config={},
            capital_allocated=self.initial_balance,
            created_at=start_date,
            updated_at=start_date,
        )

        # Track equity curve for drawdown calculation
        equity_curve = [float(self.initial_balance)]
        peak_equity = float(self.initial_balance)
        max_drawdown = Decimal("0")

        # Replay historical data
        for snapshot in historical_data:
            timestamp = snapshot["timestamp"]
            if timestamp < start_date or timestamp > end_date:
                continue

            # Create market entity from snapshot
            market = Market(
                market_id=snapshot["market_id"],
                question=snapshot["question"],
                outcomes=snapshot["outcomes"],
                liquidity=Decimal(str(snapshot["liquidity"])),
                created_at=timestamp,
                updated_at=timestamp,
            )

            yes_price = Price(Decimal(str(snapshot["yes_price"])))
            no_price = Price(Decimal(str(snapshot["no_price"])))

            # Analyze market with strategy
            signal = strategy.analyze_market(market, yes_price, no_price)

            if signal["should_enter"]:
                # Calculate position size
                position_size = strategy.calculate_position_size(
                    market=market,
                    entry_price=signal["entry_price"],
                    portfolio_value=paper_wallet.get_total_value(
                        {market.market_id: yes_price.value}
                    ),
                )

                if position_size > 0:
                    # Submit order
                    try:
                        order_id = execution_engine.submit_order(
                            market_id=market.market_id,
                            side=signal["side"],
                            size=position_size,
                            price=signal["entry_price"].value,
                            post_only=True,
                        )
                        logger.debug(
                            "Backtest order submitted",
                            extra={"order_id": str(order_id)},
                        )
                    except ValueError as e:
                        logger.warning(f"Failed to submit order: {e}")

            # Process market updates (fill orders)
            execution_engine.process_market_update(
                market_id=market.market_id,
                current_price=yes_price.value,
            )

            # Check exit conditions for open positions
            for position in paper_wallet.get_open_positions():
                if position.market_id == market.market_id:
                    # Calculate holding time
                    holding_hours = (timestamp - position.opened_at).total_seconds() / 3600

                    should_exit = strategy.should_exit(
                        entry_price=Price(position.entry_price),
                        current_price=yes_price,
                        holding_hours=holding_hours,
                        unrealized_pnl=position.calculate_unrealized_pnl(yes_price.value),
                    )

                    if should_exit:
                        # Close position
                        paper_wallet.close_position(
                            position_id=position.position_id,
                            exit_price=yes_price.value,
                        )
                        logger.debug(
                            "Backtest position closed",
                            extra={"position_id": str(position.position_id)},
                        )

            # Update equity curve
            current_equity = float(
                paper_wallet.get_total_value({market.market_id: yes_price.value})
            )
            equity_curve.append(current_equity)

            # Calculate drawdown
            if current_equity > peak_equity:
                peak_equity = current_equity
            else:
                drawdown_pct = (peak_equity - current_equity) / peak_equity * 100
                if Decimal(str(drawdown_pct)) > max_drawdown:
                    max_drawdown = Decimal(str(drawdown_pct))

        # Calculate final metrics
        stats = paper_wallet.get_statistics({})  # Empty prices since all closed
        final_balance = Decimal(str(stats["total_value"]))
        total_pnl = final_balance - self.initial_balance
        return_pct = total_pnl / self.initial_balance * 100

        closed_positions = paper_wallet.get_closed_positions()
        winning = sum(1 for pos in closed_positions if pos.realized_pnl and pos.realized_pnl > 0)
        losing = sum(1 for pos in closed_positions if pos.realized_pnl and pos.realized_pnl < 0)

        win_rate = Decimal(winning) / Decimal(len(closed_positions)) if closed_positions else Decimal("0")

        # Calculate profit factor
        total_wins = sum(
            pos.realized_pnl for pos in closed_positions if pos.realized_pnl and pos.realized_pnl > 0
        )
        total_losses = abs(
            sum(pos.realized_pnl for pos in closed_positions if pos.realized_pnl and pos.realized_pnl < 0)
        )
        profit_factor = total_wins / total_losses if total_losses > 0 else Decimal("0")

        # Calculate Sharpe ratio (simplified)
        sharpe_ratio = None
        if len(equity_curve) > 1:
            returns = [
                (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
                for i in range(1, len(equity_curve))
            ]
            if returns:
                import statistics
                avg_return = statistics.mean(returns)
                std_return = statistics.stdev(returns) if len(returns) > 1 else 0
                if std_return > 0:
                    sharpe_ratio = Decimal(str(avg_return / std_return * (252 ** 0.5)))  # Annualized

        # Build trades list
        trades = [
            {
                "position_id": str(pos.position_id),
                "market_id": pos.market_id,
                "side": pos.side,
                "size": float(pos.size),
                "entry_price": float(pos.entry_price),
                "exit_price": float(pos.exit_price) if pos.exit_price else None,
                "realized_pnl": float(pos.realized_pnl) if pos.realized_pnl else None,
                "opened_at": pos.opened_at.isoformat(),
                "closed_at": pos.closed_at.isoformat() if pos.closed_at else None,
            }
            for pos in closed_positions
        ]

        result = BacktestResult(
            strategy_name=strategy.__class__.__name__,
            start_date=start_date,
            end_date=end_date,
            initial_balance=self.initial_balance,
            final_balance=final_balance,
            total_pnl=total_pnl,
            return_pct=return_pct,
            total_trades=len(closed_positions),
            winning_trades=winning,
            losing_trades=losing,
            win_rate=win_rate,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            max_drawdown_pct=max_drawdown,
            trades=trades,
        )

        logger.info(
            "Backtest completed",
            extra={
                "total_pnl": float(total_pnl),
                "return_pct": float(return_pct),
                "win_rate": float(win_rate),
                "total_trades": len(closed_positions),
            },
        )

        return result
