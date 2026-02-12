#!/usr/bin/env python3
"""CLI script to run backtests."""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from src.application.bots.bot8_volatility_skew import Bot8VolatilitySkew
from src.infrastructure.paper_trading.backtesting.data_loader import (
    HistoricalDataLoader,
)
from src.infrastructure.paper_trading.backtesting.engine import BacktestEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def main():
    """Run backtest."""
    logger.info("Starting backtest")

    # Configuration
    market_id = "test_market_1"
    start_date = datetime.now() - timedelta(days=90)
    end_date = datetime.now()
    initial_balance = Decimal("10000")

    # Create bot
    bot_config = {
        "spread_threshold": 0.15,
        "entry_threshold_low": 0.20,
        "entry_threshold_high": 0.80,
        "hold_hours_min": 24,
        "hold_hours_max": 48,
        "target_delta": 0.30,
        "stop_loss_pct": 0.10,
    }
    bot = Bot8VolatilitySkew(config=bot_config)

    # Create engine
    engine = BacktestEngine(strategy=bot, initial_balance=initial_balance)

    # Load data
    logger.info("Loading historical data")
    data_loader = HistoricalDataLoader()
    price_data = data_loader.load_price_data(
        market_id=market_id,
        start_date=start_date,
        end_date=end_date,
    )

    # Run backtest
    logger.info("Running backtest")
    result = engine.run(
        market_id=market_id,
        start_date=start_date,
        end_date=end_date,
        price_data=price_data,
    )

    # Print results
    print("\n" + "=" * 50)
    print("BACKTEST RESULTS")
    print("=" * 50)
    print(f"Period: {result.start_date.date()} to {result.end_date.date()}")
    print(f"Initial Balance: ${result.initial_balance:,.2f}")
    print(f"Final Balance: ${result.final_balance:,.2f}")
    print(f"Total Return: ${result.total_return:,.2f} ({result.total_return_pct:.2f}%)")
    print(f"\nTrades: {result.total_trades}")
    print(f"  Winning: {result.winning_trades}")
    print(f"  Losing: {result.losing_trades}")
    print(f"  Win Rate: {result.win_rate*100:.1f}%")
    print(f"\nProfit Factor: {result.profit_factor:.2f}")
    print(f"Average Win: ${result.avg_win:,.2f}")
    print(f"Average Loss: ${result.avg_loss:,.2f}")
    print(f"Max Drawdown: {result.max_drawdown:.2f}%")
    print("=" * 50)

    # Validation against $106K evidence targets
    print("\nVALIDATION:")
    print(f"  Win Rate: {'PASS' if 0.60 <= result.win_rate <= 0.70 else 'FAIL'} (target: 60-70%)")
    print(f"  Profit Factor: {'PASS' if result.profit_factor >= 1.5 else 'FAIL'} (target: >1.5)")
    print(f"  Max Drawdown: {'PASS' if result.max_drawdown <= 15 else 'FAIL'} (target: <15%)")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
