"""Bot orchestrator for lifecycle management."""

import asyncio
import logging
from decimal import Decimal
from typing import Optional

from src.domain.entities.bot import Bot, BotState
from src.domain.protocols.repositories import BotRepository
from src.domain.services.risk_calculator import RiskCalculator

logger = logging.getLogger(__name__)


class BotOrchestrator:
    """Bot orchestrator manages bot lifecycle.

    Responsibilities:
    - Start/stop bots
    - State machine transitions
    - Circuit breaker integration
    - Event emission
    - Multi-bot coordination

    Example:
        >>> orchestrator = BotOrchestrator(bot_repo, risk_calc)
        >>> await orchestrator.start_bot(bot_id=1)
        >>> await orchestrator.stop_bot(bot_id=1)
    """

    def __init__(
        self,
        bot_repository: BotRepository,
        risk_calculator: RiskCalculator,
    ) -> None:
        """Initialize orchestrator.

        Args:
            bot_repository: Bot repository
            risk_calculator: Risk calculator
        """
        self.bot_repo = bot_repository
        self.risk_calc = risk_calculator
        self._running_bots: dict[int, asyncio.Task] = {}

    async def start_bot(self, bot_id: int) -> None:
        """Start bot.

        Args:
            bot_id: Bot ID

        Raises:
            ValueError: If bot already running or not found
        """
        if bot_id in self._running_bots:
            raise ValueError(f"Bot {bot_id} already running")

        # Get bot
        bot_data = await self.bot_repo.get_by_id(bot_id)
        if not bot_data:
            raise ValueError(f"Bot {bot_id} not found")

        # Validate state
        current_state = BotState(bot_data["state"])
        if current_state not in (BotState.IDLE, BotState.STOPPED):
            raise ValueError(f"Bot {bot_id} in invalid state: {current_state.value}")

        # Transition to ANALYZING
        await self._transition_bot_state(bot_id, BotState.ANALYZING)

        # Start bot task
        task = asyncio.create_task(self._bot_loop(bot_id))
        self._running_bots[bot_id] = task

        logger.info("Bot started", extra={"bot_id": bot_id})

    async def stop_bot(self, bot_id: int, emergency: bool = False) -> None:
        """Stop bot.

        Args:
            bot_id: Bot ID
            emergency: Emergency stop (skip graceful shutdown)

        Raises:
            ValueError: If bot not running
        """
        if bot_id not in self._running_bots:
            raise ValueError(f"Bot {bot_id} not running")

        # Cancel task
        task = self._running_bots[bot_id]
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        del self._running_bots[bot_id]

        # Transition to STOPPED
        target_state = BotState.ERROR if emergency else BotState.STOPPED
        await self._transition_bot_state(bot_id, target_state)

        logger.info(
            "Bot stopped",
            extra={"bot_id": bot_id, "emergency": emergency},
        )

    async def _bot_loop(self, bot_id: int) -> None:
        """Main bot loop.

        Args:
            bot_id: Bot ID
        """
        try:
            while True:
                # Get bot state
                bot_data = await self.bot_repo.get_by_id(bot_id)
                if not bot_data:
                    break

                state = BotState(bot_data["state"])

                # State machine
                if state == BotState.ANALYZING:
                    # Analyze markets
                    # If opportunity found, transition to PLACING
                    # Otherwise stay in ANALYZING
                    pass

                elif state == BotState.PLACING:
                    # Place orders
                    # When order filled, transition to HOLDING
                    pass

                elif state == BotState.HOLDING:
                    # Monitor positions
                    # When exit signal, transition to EXITING
                    pass

                elif state == BotState.EXITING:
                    # Close positions
                    # When closed, transition to IDLE
                    pass

                elif state == BotState.IDLE:
                    # Wait for next cycle
                    await asyncio.sleep(60)
                    await self._transition_bot_state(bot_id, BotState.ANALYZING)

                else:
                    # Invalid state
                    break

                await asyncio.sleep(10)  # Bot cycle interval

        except asyncio.CancelledError:
            logger.info("Bot loop cancelled", extra={"bot_id": bot_id})
        except Exception as e:
            logger.error(
                "Bot loop error",
                extra={"bot_id": bot_id, "error": str(e)},
            )
            await self._transition_bot_state(bot_id, BotState.ERROR)

    async def _transition_bot_state(
        self,
        bot_id: int,
        new_state: BotState,
    ) -> None:
        """Transition bot state.

        Args:
            bot_id: Bot ID
            new_state: Target state

        Raises:
            ValueError: If transition invalid
        """
        # Get current state
        bot_data = await self.bot_repo.get_by_id(bot_id)
        if not bot_data:
            raise ValueError(f"Bot {bot_id} not found")

        current_state = BotState(bot_data["state"])

        # Validate transition
        from datetime import datetime

        bot = Bot(
            bot_id=bot_id,
            strategy_type=bot_data["strategy_type"],
            state=current_state,
            config=bot_data["config"],
            capital_allocated=Decimal(str(bot_data["capital_allocated"])),
            created_at=bot_data["created_at"],
            updated_at=datetime.now(),
        )

        if not bot.can_transition_to(new_state):
            raise ValueError(
                f"Invalid state transition: {current_state.value} -> {new_state.value}"
            )

        # Update state
        await self.bot_repo.update_state(bot_id, new_state.value)

        logger.info(
            "Bot state transition",
            extra={
                "bot_id": bot_id,
                "from_state": current_state.value,
                "to_state": new_state.value,
            },
        )

    async def check_circuit_breakers(self, bot_id: int) -> tuple[bool, Optional[str]]:
        """Check circuit breakers for bot.

        Args:
            bot_id: Bot ID

        Returns:
            Tuple of (should_stop, reason)
        """
        # Get bot metrics (simplified - real implementation queries DB)
        consecutive_losses = 0
        daily_loss_pct = Decimal("0.0")
        bot_drawdown_pct = Decimal("0.0")
        portfolio_drawdown_pct = Decimal("0.0")

        return self.risk_calc.check_circuit_breaker(
            consecutive_losses=consecutive_losses,
            daily_loss_pct=daily_loss_pct,
            bot_drawdown_pct=bot_drawdown_pct,
            portfolio_drawdown_pct=portfolio_drawdown_pct,
        )
