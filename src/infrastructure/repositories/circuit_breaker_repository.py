"""Circuit breaker repository."""

import json
import logging
from decimal import Decimal

from src.infrastructure.persistence.redis_client import RedisClient

logger = logging.getLogger(__name__)


class CircuitBreakerRepository:
    """Repository for circuit breaker state.

    Stores circuit breaker state in Redis for fast access and updates.
    """

    def __init__(self, redis: RedisClient):
        """Initialize repository.

        Args:
            redis: Redis client
        """
        self.redis = redis
        self.breaker_key_prefix = "circuit_breaker:bot:"
        self.portfolio_key = "circuit_breaker:portfolio"

    async def get_bot_state(self, bot_id: int) -> dict:
        """Get bot circuit breaker state.

        Args:
            bot_id: Bot ID

        Returns:
            Circuit breaker state dict
        """
        key = f"{self.breaker_key_prefix}{bot_id}"
        data = await self.redis.get(key)

        if not data:
            # Initialize default state
            return {
                "consecutive_losses": 0,
                "daily_pnl": "0.0",
                "bot_drawdown_pct": "0.0",
                "is_stopped": False,
            }

        return json.loads(data)

    async def save_bot_state(self, bot_id: int, state: dict) -> None:
        """Save bot circuit breaker state.

        Args:
            bot_id: Bot ID
            state: Circuit breaker state
        """
        key = f"{self.breaker_key_prefix}{bot_id}"
        await self.redis.set(key, json.dumps(state))

        logger.debug(
            "Bot circuit breaker state saved",
            extra={"bot_id": bot_id, "state": state},
        )

    async def increment_consecutive_losses(self, bot_id: int) -> int:
        """Increment consecutive losses atomically.

        Args:
            bot_id: Bot ID

        Returns:
            New consecutive losses count
        """
        state = await self.get_bot_state(bot_id)
        state["consecutive_losses"] += 1
        await self.save_bot_state(bot_id, state)

        return state["consecutive_losses"]

    async def reset_consecutive_losses(self, bot_id: int) -> None:
        """Reset consecutive losses to 0.

        Args:
            bot_id: Bot ID
        """
        state = await self.get_bot_state(bot_id)
        state["consecutive_losses"] = 0
        await self.save_bot_state(bot_id, state)

        logger.info(
            "Consecutive losses reset",
            extra={"bot_id": bot_id},
        )

    async def update_daily_pnl(self, bot_id: int, daily_pnl: Decimal) -> None:
        """Update daily P&L.

        Args:
            bot_id: Bot ID
            daily_pnl: Daily P&L
        """
        state = await self.get_bot_state(bot_id)
        state["daily_pnl"] = str(daily_pnl)
        await self.save_bot_state(bot_id, state)

    async def update_bot_drawdown(self, bot_id: int, drawdown_pct: Decimal) -> None:
        """Update bot drawdown.

        Args:
            bot_id: Bot ID
            drawdown_pct: Drawdown percentage
        """
        state = await self.get_bot_state(bot_id)
        state["bot_drawdown_pct"] = str(drawdown_pct)
        await self.save_bot_state(bot_id, state)

    async def stop_bot(self, bot_id: int, reason: str) -> None:
        """Stop bot (set flag).

        Args:
            bot_id: Bot ID
            reason: Stop reason
        """
        state = await self.get_bot_state(bot_id)
        state["is_stopped"] = True
        state["stop_reason"] = reason
        await self.save_bot_state(bot_id, state)

        logger.warning(
            "Bot stopped by circuit breaker",
            extra={"bot_id": bot_id, "reason": reason},
        )

    async def is_bot_stopped(self, bot_id: int) -> bool:
        """Check if bot is stopped.

        Args:
            bot_id: Bot ID

        Returns:
            True if bot is stopped
        """
        state = await self.get_bot_state(bot_id)
        return state.get("is_stopped", False)

    async def get_portfolio_state(self) -> dict:
        """Get portfolio circuit breaker state.

        Returns:
            Portfolio state dict
        """
        data = await self.redis.get(self.portfolio_key)

        if not data:
            return {
                "portfolio_drawdown_pct": "0.0",
                "emergency_stop": False,
            }

        return json.loads(data)

    async def save_portfolio_state(self, state: dict) -> None:
        """Save portfolio circuit breaker state.

        Args:
            state: Portfolio state
        """
        await self.redis.set(self.portfolio_key, json.dumps(state))

        logger.debug("Portfolio circuit breaker state saved", extra={"state": state})

    async def update_portfolio_drawdown(self, drawdown_pct: Decimal) -> None:
        """Update portfolio drawdown.

        Args:
            drawdown_pct: Drawdown percentage
        """
        state = await self.get_portfolio_state()
        state["portfolio_drawdown_pct"] = str(drawdown_pct)
        await self.save_portfolio_state(state)

    async def trigger_emergency_stop(self, reason: str) -> None:
        """Trigger emergency stop.

        Args:
            reason: Emergency stop reason
        """
        state = await self.get_portfolio_state()
        state["emergency_stop"] = True
        state["emergency_reason"] = reason
        await self.save_portfolio_state(state)

        logger.error(
            "EMERGENCY STOP TRIGGERED",
            extra={"reason": reason},
        )

    async def is_emergency_stopped(self) -> bool:
        """Check if emergency stop is active.

        Returns:
            True if emergency stop active
        """
        state = await self.get_portfolio_state()
        return state.get("emergency_stop", False)
