"""Circuit breaker enforcement for production trading."""

import logging
from decimal import Decimal

from src.domain.services.circuit_breaker_checker import CircuitBreakerChecker, CircuitBreakerStatus
from src.infrastructure.repositories.circuit_breaker_repository import CircuitBreakerRepository

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit breaker enforcement.

    Enforces all safety limits before allowing trades:
    1. 3 consecutive losses → STOP bot
    2. 5% daily loss → STOP bot
    3. 25% bot drawdown → STOP bot
    4. 40% portfolio drawdown → EMERGENCY STOP ALL
    5. Z4-Z5 directional trades → BLOCK
    """

    def __init__(
        self,
        checker: CircuitBreakerChecker,
        repository: CircuitBreakerRepository,
    ):
        """Initialize circuit breaker.

        Args:
            checker: Circuit breaker checker
            repository: Circuit breaker repository
        """
        self.checker = checker
        self.repository = repository

    async def check_before_trade(
        self,
        bot_id: int,
        zone: int,
        portfolio_value: Decimal,
        portfolio_peak: Decimal,
    ) -> tuple[bool, str]:
        """Check if trade is allowed.

        Args:
            bot_id: Bot ID
            zone: Risk zone
            portfolio_value: Current portfolio value
            portfolio_peak: Portfolio peak value

        Returns:
            Tuple of (is_allowed, reason)
        """
        # Check if bot already stopped
        if await self.repository.is_bot_stopped(bot_id):
            return False, "Bot stopped by circuit breaker"

        # Check if emergency stop active
        if await self.repository.is_emergency_stopped():
            return False, "Emergency stop active"

        # Get bot state
        bot_state = await self.repository.get_bot_state(bot_id)
        consecutive_losses = bot_state["consecutive_losses"]
        daily_pnl_pct = Decimal(bot_state["daily_pnl"])
        bot_drawdown_pct = Decimal(bot_state["bot_drawdown_pct"])

        # Calculate portfolio drawdown
        portfolio_drawdown_pct = (
            (portfolio_peak - portfolio_value) / portfolio_peak * Decimal("100")
            if portfolio_peak > 0
            else Decimal("0")
        )

        # Update portfolio drawdown
        await self.repository.update_portfolio_drawdown(portfolio_drawdown_pct)

        # Check all conditions
        is_allowed, reason = self.checker.check_before_trade(
            bot_id=bot_id,
            zone=zone,
            consecutive_losses=consecutive_losses,
            daily_pnl_pct=daily_pnl_pct,
            bot_drawdown_pct=bot_drawdown_pct,
            portfolio_drawdown_pct=portfolio_drawdown_pct,
        )

        if not is_allowed:
            # Stop bot if breaker triggered
            if "EMERGENCY" in reason:
                await self.repository.trigger_emergency_stop(reason)
            else:
                await self.repository.stop_bot(bot_id, reason)

        return is_allowed, reason

    async def record_trade_result(
        self,
        bot_id: int,
        pnl: Decimal,
        position_size: Decimal,
    ) -> None:
        """Record trade result and update state.

        Args:
            bot_id: Bot ID
            pnl: Realized P&L
            position_size: Position size
        """
        is_win = pnl > 0

        # Get current state
        bot_state = await self.repository.get_bot_state(bot_id)
        consecutive_losses = bot_state["consecutive_losses"]

        # Update consecutive losses
        new_consecutive_losses = self.checker.record_trade_result(
            bot_id=bot_id,
            is_win=is_win,
            consecutive_losses=consecutive_losses,
        )

        # Save updated state
        bot_state["consecutive_losses"] = new_consecutive_losses
        await self.repository.save_bot_state(bot_id, bot_state)

        logger.info(
            "Trade result recorded",
            extra={
                "bot_id": bot_id,
                "pnl": float(pnl),
                "is_win": is_win,
                "consecutive_losses": new_consecutive_losses,
            },
        )

    async def get_status(self, bot_id: int) -> CircuitBreakerStatus:
        """Get circuit breaker status for bot.

        Args:
            bot_id: Bot ID

        Returns:
            Circuit breaker status
        """
        bot_state = await self.repository.get_bot_state(bot_id)
        portfolio_state = await self.repository.get_portfolio_state()

        is_stopped = bot_state.get("is_stopped", False)
        reason = bot_state.get("stop_reason", "")

        if await self.repository.is_emergency_stopped():
            is_stopped = True
            reason = "Emergency stop active"

        return CircuitBreakerStatus(
            bot_id=bot_id,
            is_active=is_stopped,
            reason=reason,
            consecutive_losses=bot_state["consecutive_losses"],
            daily_pnl_pct=Decimal(bot_state["daily_pnl"]),
            bot_drawdown_pct=Decimal(bot_state["bot_drawdown_pct"]),
            portfolio_drawdown_pct=Decimal(portfolio_state["portfolio_drawdown_pct"]),
        )

    async def reset_bot(self, bot_id: int) -> None:
        """Reset bot circuit breaker (admin override).

        Args:
            bot_id: Bot ID
        """
        await self.repository.reset_consecutive_losses(bot_id)

        bot_state = await self.repository.get_bot_state(bot_id)
        bot_state["is_stopped"] = False
        bot_state.pop("stop_reason", None)
        await self.repository.save_bot_state(bot_id, bot_state)

        logger.info(
            "Bot circuit breaker reset",
            extra={"bot_id": bot_id},
        )
