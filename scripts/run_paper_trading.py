#!/usr/bin/env python3
"""CLI script to run paper trading."""

import asyncio
import logging
from decimal import Decimal

from src.application.use_cases.run_paper_trading import RunPaperTradingUseCase

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def main():
    """Run paper trading."""
    logger.info("Starting paper trading")

    # Configuration
    session_id = "cli_session"
    initial_balance = Decimal("10000")

    bot_config = {
        "spread_threshold": 0.15,
        "entry_threshold_low": 0.20,
        "entry_threshold_high": 0.80,
        "hold_hours_min": 24,
        "hold_hours_max": 48,
        "target_delta": 0.30,
        "stop_loss_pct": 0.10,
    }

    # Create use case
    use_case = RunPaperTradingUseCase()

    # Start session
    session = await use_case.start_session(
        session_id=session_id,
        initial_balance=initial_balance,
        bot_config=bot_config,
    )

    logger.info(f"Paper trading session {session_id} started")
    logger.info(f"Initial balance: ${initial_balance}")
    logger.info("Press Ctrl+C to stop")

    try:
        # Keep running until Ctrl+C
        while True:
            await asyncio.sleep(10)
            
            # Print status
            stats = session.wallet.get_statistics()
            logger.info(
                f"Status: Balance=${stats['current_balance']:,.2f} | "
                f"Total Value=${stats['total_value']:,.2f} | "
                f"P&L=${stats['total_pnl']:,.2f} | "
                f"Open={stats['open_positions']} | "
                f"Closed={stats['closed_positions']} | "
                f"Win Rate={stats['win_rate']*100:.1f}%"
            )
    except KeyboardInterrupt:
        logger.info("\nStopping paper trading...")
        await use_case.stop_session(session_id)
        
        # Print final stats
        stats = session.wallet.get_statistics()
        print("\n" + "=" * 50)
        print("PAPER TRADING RESULTS")
        print("=" * 50)
        print(f"Initial Balance: ${stats['initial_balance']:,.2f}")
        print(f"Final Balance: ${stats['current_balance']:,.2f}")
        print(f"Total Value: ${stats['total_value']:,.2f}")
        print(f"Total P&L: ${stats['total_pnl']:,.2f} ({stats['return_pct']:.2f}%)")
        print(f"\nPositions:")
        print(f"  Open: {stats['open_positions']}")
        print(f"  Closed: {stats['closed_positions']}")
        print(f"\nTrades: {stats['total_trades']}")
        print(f"  Winning: {stats['winning_trades']}")
        print(f"  Losing: {stats['losing_trades']}")
        print(f"  Win Rate: {stats['win_rate']*100:.1f}%")
        print("=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
