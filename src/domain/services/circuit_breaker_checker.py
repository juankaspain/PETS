"""Circuit breaker checker service."""

import logging
from dataclasses import dataclass
from decimal import Decimal

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerStatus:
    """Circuit breaker status."""

    bot_id: int
    is_active: bool
    reason: str
    consecutive_losses: int
    daily_pnl_pct: Decimal
    bot_drawdown_pct: Decimal
    portfolio_drawdown_pct: Decimal


class CircuitBreakerChecker:
    """Service to check circuit breaker conditions.

    Enforces:
    1. 3 consecutive losses → STOP bot
    2. 5% daily loss → STOP bot
    3. 25% bot drawdown → STOP bot
    4. 40% portfolio drawdown → EMERGENCY STOP ALL
    5. Z4-Z5 directional trades → BLOCK
    """

    def __init__(self):
        """Initialize circuit breaker checker."""
        # Thresholds
        self.max_consecutive_losses = 3
        self.max_daily_loss_pct = Decimal("5.0")  # 5%
        self.max_bot_drawdown_pct = Decimal("25.0")  # 25%
        self.max_portfolio_drawdown_pct = Decimal("40.0")  # 40%
        self.safe_zones = [1, 2, 3]  # Only Z1-Z3 allowed

    def check_before_trade(
        self,
        bot_id: int,
        zone: int,
        consecutive_losses: int,
        daily_pnl_pct: Decimal,
        bot_drawdown_pct: Decimal,
        portfolio_drawdown_pct: Decimal,
    ) -> tuple[bool, str]:
        """Check if trade is allowed.

        Args:
            bot_id: Bot ID
            zone: Risk zone (1-5)
            consecutive_losses: Consecutive losses count
            daily_pnl_pct: Daily P&L percentage
            bot_drawdown_pct: Bot drawdown percentage
            portfolio_drawdown_pct: Portfolio drawdown percentage

        Returns:
            Tuple of (is_allowed, reason)
        """
        # 1. Check consecutive losses
        if consecutive_losses >= self.max_consecutive_losses:
            reason = f"Circuit breaker: {consecutive_losses} consecutive losses (max {self.max_consecutive_losses})"
            logger.warning(
                reason,
                extra={"bot_id": bot_id, "consecutive_losses": consecutive_losses},
            )
            return False, reason

        # 2. Check daily loss
        if daily_pnl_pct <= -self.max_daily_loss_pct:
            reason = f"Circuit breaker: {daily_pnl_pct:.1f}% daily loss (max {self.max_daily_loss_pct}%)"
            logger.warning(
                reason,
                extra={"bot_id": bot_id, "daily_pnl_pct": float(daily_pnl_pct)},
            )
            return False, reason

        # 3. Check bot drawdown
        if bot_drawdown_pct >= self.max_bot_drawdown_pct:
            reason = f"Circuit breaker: {bot_drawdown_pct:.1f}% bot drawdown (max {self.max_bot_drawdown_pct}%)"
            logger.warning(
                reason,
                extra={"bot_id": bot_id, "bot_drawdown_pct": float(bot_drawdown_pct)},
            )
            return False, reason

        # 4. Check portfolio drawdown (EMERGENCY)
        if portfolio_drawdown_pct >= self.max_portfolio_drawdown_pct:
            reason = f"EMERGENCY STOP: {portfolio_drawdown_pct:.1f}% portfolio drawdown (max {self.max_portfolio_drawdown_pct}%)"
            logger.error(
                reason,
                extra={"portfolio_drawdown_pct": float(portfolio_drawdown_pct)},
            )
            return False, reason

        # 5. Check zone (Z4-Z5 directional PROHIBITED)
        if zone not in self.safe_zones:
            reason = f"Circuit breaker: Zone {zone} not allowed (only Z1-Z3)"
            logger.warning(
                reason,
                extra={"bot_id": bot_id, "zone": zone},
            )
            return False, reason

        # All checks passed
        return True, ""

    def check_emergency_stop(
        self,
        portfolio_drawdown_pct: Decimal,
    ) -> bool:
        """Check if emergency stop should be triggered.

        Args:
            portfolio_drawdown_pct: Portfolio drawdown percentage

        Returns:
            True if emergency stop required
        """
        if portfolio_drawdown_pct >= self.max_portfolio_drawdown_pct:
            logger.error(
                "EMERGENCY STOP TRIGGERED",
                extra={"portfolio_drawdown_pct": float(portfolio_drawdown_pct)},
            )
            return True

        return False

    def record_trade_result(
        self,
        bot_id: int,
        is_win: bool,
        consecutive_losses: int,
    ) -> int:
        """Record trade result and update consecutive losses.

        Args:
            bot_id: Bot ID
            is_win: True if trade was profitable
            consecutive_losses: Current consecutive losses

        Returns:
            Updated consecutive losses count
        """
        if is_win:
            # Reset consecutive losses on win
            logger.info(
                "Win: Resetting consecutive losses",
                extra={"bot_id": bot_id},
            )
            return 0
        else:
            # Increment consecutive losses
            new_count = consecutive_losses + 1
            logger.warning(
                "Loss: Incrementing consecutive losses",
                extra={"bot_id": bot_id, "consecutive_losses": new_count},
            )
            return new_count
