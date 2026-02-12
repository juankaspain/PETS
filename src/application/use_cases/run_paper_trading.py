"""Run paper trading use case."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict

from src.application.bots.bot8_volatility_skew import Bot8VolatilitySkew
from src.infrastructure.paper_trading.paper_wallet import PaperWallet
from src.infrastructure.paper_trading.market_simulator import MarketSimulator
from src.infrastructure.paper_trading.simulated_executor import SimulatedOrderExecutor

logger = logging.getLogger(__name__)


@dataclass
class PaperTradingSession:
    """Paper trading session."""

    session_id: str
    started_at: datetime
    initial_balance: Decimal
    wallet: PaperWallet
    market_simulator: MarketSimulator
    executor: SimulatedOrderExecutor
    bot: Bot8VolatilitySkew
    is_running: bool = True


class RunPaperTradingUseCase:
    """Use case for running real-time paper trading.

    Orchestrates:
    - Market data simulation/feed
    - Bot 8 strategy execution
    - Order placement and fills
    - Position management
    - Performance tracking
    """

    def __init__(self):
        """Initialize use case."""
        self.sessions: Dict[str, PaperTradingSession] = {}

        logger.info("RunPaperTradingUseCase initialized")

    async def start_session(
        self,
        session_id: str,
        initial_balance: Decimal = Decimal("10000"),
        bot_config: dict | None = None,
    ) -> PaperTradingSession:
        """Start paper trading session.

        Args:
            session_id: Session ID
            initial_balance: Starting balance
            bot_config: Bot configuration (optional)

        Returns:
            Paper trading session
        """
        logger.info(
            "Starting paper trading session",
            extra={
                "session_id": session_id,
                "initial_balance": float(initial_balance),
            },
        )

        # Create components
        wallet = PaperWallet(initial_balance)
        market_simulator = MarketSimulator()
        executor = SimulatedOrderExecutor()

        # Create Bot 8
        if bot_config is None:
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

        # Create session
        session = PaperTradingSession(
            session_id=session_id,
            started_at=datetime.utcnow(),
            initial_balance=initial_balance,
            wallet=wallet,
            market_simulator=market_simulator,
            executor=executor,
            bot=bot,
            is_running=True,
        )

        self.sessions[session_id] = session

        # Start trading loop in background
        asyncio.create_task(self._trading_loop(session))

        logger.info(
            "Paper trading session started",
            extra={"session_id": session_id},
        )

        return session

    async def stop_session(self, session_id: str) -> None:
        """Stop paper trading session.

        Args:
            session_id: Session ID

        Raises:
            ValueError: If session not found
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.is_running = False

        # Close all open positions
        for position in session.wallet.open_positions:
            current_price = session.market_simulator.get_current_price(
                position.market_id
            )
            session.wallet.close_position(position.position_id, current_price)

        logger.info(
            "Paper trading session stopped",
            extra={
                "session_id": session_id,
                "final_balance": float(session.wallet.total_value),
                "total_pnl": float(session.wallet.total_pnl),
            },
        )

    def get_session(self, session_id: str) -> PaperTradingSession | None:
        """Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session or None
        """
        return self.sessions.get(session_id)

    async def _trading_loop(self, session: PaperTradingSession) -> None:
        """Main trading loop for session.

        Args:
            session: Paper trading session
        """
        logger.info(
            "Trading loop started",
            extra={"session_id": session.session_id},
        )

        # Add test market
        test_market_id = "test_market_1"
        session.market_simulator.add_market(
            market_id=test_market_id,
            initial_yes_price=Decimal("0.15"),  # Start with opportunity
            initial_no_price=Decimal("0.85"),
            liquidity=Decimal("100000"),
        )

        iteration = 0

        while session.is_running:
            iteration += 1

            # Simulate price movement (random walk with mean reversion)
            import random

            current_price = session.market_simulator.get_current_price(
                test_market_id
            )
            change = Decimal(str(random.gauss(0, 0.01)))  # 1% std dev
            mean_reversion = (Decimal("0.50") - current_price) * Decimal("0.05")
            new_price = current_price + change + mean_reversion
            new_price = max(Decimal("0.01"), min(Decimal("0.99"), new_price))

            session.market_simulator.update_price(test_market_id, new_price)
            snapshot = session.market_simulator.get_snapshot(test_market_id)

            # Check if Bot 8 wants to enter
            if not session.wallet.open_positions:
                should_enter, entry_side = session.bot.analyze_market(
                    market_id=test_market_id,
                    yes_price=float(snapshot.yes_price),
                    no_price=float(snapshot.no_price),
                    liquidity=float(snapshot.liquidity),
                )

                if should_enter:
                    # Calculate position size (15% of portfolio)
                    position_size = session.wallet.balance * Decimal("0.15")

                    # Open position
                    try:
                        position = session.wallet.open_position(
                            market_id=test_market_id,
                            side=entry_side,
                            size=position_size,
                            price=snapshot.yes_price
                            if entry_side == "BUY"
                            else snapshot.no_price,
                        )
                        logger.info(
                            "Position opened in paper trading",
                            extra={
                                "session_id": session.session_id,
                                "position_id": str(position.position_id),
                                "side": entry_side,
                                "price": float(snapshot.yes_price),
                            },
                        )
                    except ValueError as e:
                        logger.warning(f"Failed to open position: {e}")

            # Check if Bot 8 wants to exit
            for position in session.wallet.open_positions:
                holding_hours = (
                    (datetime.utcnow() - position.opened_at).total_seconds() / 3600
                )

                should_exit = session.bot.should_exit(
                    position_id=str(position.position_id),
                    entry_price=float(position.entry_price),
                    current_price=float(snapshot.yes_price),
                    holding_hours=holding_hours,
                )

                if should_exit:
                    session.wallet.close_position(
                        position_id=position.position_id,
                        exit_price=snapshot.yes_price,
                    )
                    logger.info(
                        "Position closed in paper trading",
                        extra={
                            "session_id": session.session_id,
                            "position_id": str(position.position_id),
                            "holding_hours": holding_hours,
                        },
                    )

            # Log status every 10 iterations
            if iteration % 10 == 0:
                stats = session.wallet.get_statistics()
                logger.info(
                    "Paper trading status",
                    extra={
                        "session_id": session.session_id,
                        "iteration": iteration,
                        "balance": float(session.wallet.balance),
                        "total_value": float(session.wallet.total_value),
                        "total_pnl": float(session.wallet.total_pnl),
                        "open_positions": len(session.wallet.open_positions),
                        "closed_positions": len(session.wallet.closed_positions),
                    },
                )

            # Sleep 1 second (simulate 1 hour in accelerated mode)
            await asyncio.sleep(1)

        logger.info(
            "Trading loop stopped",
            extra={"session_id": session.session_id},
        )
