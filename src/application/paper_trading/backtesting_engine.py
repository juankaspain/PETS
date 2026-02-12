"""Backtesting engine for strategy validation."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from src.application.bots.bot8_volatility_skew import Bot8VolatilitySkew
from src.domain.entities.paper_position import PaperPosition
from src.domain.entities.paper_wallet import PaperWallet

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Backtest result."""

    backtest_id: str
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
    max_drawdown_pct: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    avg_trade_duration_hours: float
    parameters: dict[str, Any]


class BacktestingEngine:
    """Backtesting engine for historical strategy validation.
    
    Features:
    - Replay historical market data
    - Execute Bot 8 strategy
    - Calculate performance metrics
    - Compare with $106K evidence
    - Parameter optimization
    """

    def __init__(self):
        """Initialize backtesting engine."""
        self.bot8 = Bot8VolatilitySkew()

    async def run_backtest(
        self,
        start_date: datetime,
        end_date: datetime,
        initial_balance: Decimal = Decimal("10000"),
        parameters: dict[str, Any] | None = None,
    ) -> BacktestResult:
        """Run backtest on historical data.
        
        Args:
            start_date: Start date
            end_date: End date
            initial_balance: Starting balance
            parameters: Strategy parameters override
            
        Returns:
            Backtest result
        """
        logger.info(
            "Starting backtest",
            extra={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "initial_balance": float(initial_balance),
            },
        )
        
        # Initialize virtual wallet
        wallet = PaperWallet(
            balance=initial_balance,
            initial_balance=initial_balance,
        )
        
        # Override strategy parameters if provided
        if parameters:
            self.bot8.config.update(parameters)
        
        # Fetch historical data
        historical_data = await self.fetch_historical_data(start_date, end_date)
        
        logger.info(f"Fetched {len(historical_data)} historical market snapshots")
        
        # Replay historical data
        positions = []
        closed_positions = []
        
        for snapshot in historical_data:
            # Check entry signals
            signal = self.bot8.analyze_market(
                market_id=snapshot["market_id"],
                yes_price=snapshot["yes_price"],
                no_price=snapshot["no_price"],
                liquidity=snapshot["liquidity"],
            )
            
            if signal and wallet.balance > 0:
                # Open position
                position = self.simulate_position_open(
                    wallet,
                    signal,
                    snapshot["timestamp"],
                )
                positions.append(position)
                wallet = wallet.deduct(position.cost_basis)
            
            # Check exit signals for open positions
            for position in positions:
                if position.is_open:
                    hours_held = (
                        snapshot["timestamp"] - position.opened_at
                    ).total_seconds() / 3600
                    
                    should_exit, reason = self.bot8.should_exit(
                        entry_price=float(position.entry_price),
                        current_price=snapshot["yes_price"],
                        hours_held=hours_held,
                        side=position.side,
                    )
                    
                    if should_exit:
                        # Close position
                        closed_position = position.close(
                            Decimal(str(snapshot["yes_price"]))
                        )
                        closed_positions.append(closed_position)
                        wallet = wallet.add(
                            closed_position.size * closed_position.exit_price
                        )
                        wallet = wallet.record_trade(closed_position.realized_pnl)
        
        # Calculate metrics
        result = self.calculate_metrics(
            wallet,
            closed_positions,
            start_date,
            end_date,
            parameters or {},
        )
        
        logger.info(
            "Backtest complete",
            extra={
                "final_balance": float(result.final_balance),
                "total_return_pct": float(result.total_return_pct),
                "win_rate": float(result.win_rate),
                "profit_factor": float(result.profit_factor),
            },
        )
        
        return result

    async def fetch_historical_data(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict]:
        """Fetch historical market data.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of market snapshots
        """
        # TODO: Fetch from Polymarket API or TimescaleDB
        # For now, generate mock data
        
        logger.warning("Using mock historical data - implement real data fetching")
        
        data = []
        current_date = start_date
        
        while current_date <= end_date:
            # Generate mock market snapshot
            snapshot = {
                "timestamp": current_date,
                "market_id": "mock_market_123",
                "yes_price": 0.15 + (hash(current_date) % 100) / 1000,  # Mock price
                "no_price": 0.85 - (hash(current_date) % 100) / 1000,
                "liquidity": 50000,
            }
            data.append(snapshot)
            
            current_date += timedelta(hours=1)  # Hourly snapshots
        
        return data

    def simulate_position_open(
        self,
        wallet: PaperWallet,
        signal: dict,
        timestamp: datetime,
    ) -> PaperPosition:
        """Simulate opening a position.
        
        Args:
            wallet: Paper wallet
            signal: Entry signal
            timestamp: Entry timestamp
            
        Returns:
            New paper position
        """
        # Calculate position size (simplified)
        size = min(wallet.balance * Decimal("0.15"), Decimal("1500"))  # 15% max
        
        return PaperPosition(
            wallet_id=wallet.wallet_id,
            market_id=signal["market_id"],
            side=signal["side"],
            size=size,
            entry_price=Decimal(str(signal["entry_price"])),
            zone=signal["zone"],
            opened_at=timestamp,
        )

    def calculate_metrics(
        self,
        wallet: PaperWallet,
        positions: list[PaperPosition],
        start_date: datetime,
        end_date: datetime,
        parameters: dict,
    ) -> BacktestResult:
        """Calculate backtest metrics.
        
        Args:
            wallet: Final wallet state
            positions: Closed positions
            start_date: Start date
            end_date: End date
            parameters: Strategy parameters
            
        Returns:
            Backtest result
        """
        # Wins and losses
        wins = [p for p in positions if p.realized_pnl and p.realized_pnl > 0]
        losses = [p for p in positions if p.realized_pnl and p.realized_pnl < 0]
        
        total_wins = sum(p.realized_pnl for p in wins)
        total_losses = sum(abs(p.realized_pnl) for p in losses)
        
        # Metrics
        profit_factor = total_wins / total_losses if total_losses > 0 else Decimal("0")
        avg_win = total_wins / len(wins) if wins else Decimal("0")
        avg_loss = total_losses / len(losses) if losses else Decimal("0")
        
        # Trade duration
        durations = [
            (p.closed_at - p.opened_at).total_seconds() / 3600
            for p in positions
            if p.closed_at
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # TODO: Calculate Sharpe ratio and max drawdown
        sharpe_ratio = None
        max_drawdown_pct = Decimal("0")
        
        from uuid import uuid4
        
        return BacktestResult(
            backtest_id=str(uuid4()),
            start_date=start_date,
            end_date=end_date,
            initial_balance=wallet.initial_balance,
            final_balance=wallet.balance,
            total_return=wallet.realized_pnl,
            total_return_pct=wallet.total_return_pct,
            total_trades=len(positions),
            winning_trades=len(wins),
            losing_trades=len(losses),
            win_rate=wallet.win_rate,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            max_drawdown_pct=max_drawdown_pct,
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_trade_duration_hours=avg_duration,
            parameters=parameters,
        )
