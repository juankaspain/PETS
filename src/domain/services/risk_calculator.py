"""Risk calculator domain service."""

from decimal import Decimal
from typing import Optional

from src.domain.entities.order import Order
from src.domain.entities.position import Position
from src.domain.value_objects.risk import Risk


class RiskCalculator:
    """Risk calculator for position and portfolio risk.

    Enforces:
    - Zone 4-5 directional PROHIBITED
    - Max position size: 15% portfolio
    - Max bot drawdown: 25%
    - Max portfolio drawdown: 40%
    - Circuit breakers: 3 losses, 5% daily loss

    Example:
        >>> calc = RiskCalculator()
        >>> risk = calc.calculate_position_risk(
        ...     position_size=Decimal("1000"),
        ...     portfolio_value=Decimal("10000"),
        ... )
        >>> risk.percentage()
        Decimal('10.0')
    """

    # Risk limits
    MAX_POSITION_SIZE_PCT = Decimal("0.15")  # 15% max position
    MAX_BOT_DRAWDOWN_PCT = Decimal("0.25")  # 25% max bot drawdown
    MAX_PORTFOLIO_DRAWDOWN_PCT = Decimal("0.40")  # 40% max portfolio drawdown
    MAX_DAILY_LOSS_PCT = Decimal("0.05")  # 5% max daily loss
    MAX_CONSECUTIVE_LOSSES = 3  # Stop after 3 losses

    @staticmethod
    def calculate_position_risk(
        position_size: Decimal,
        portfolio_value: Decimal,
    ) -> Risk:
        """Calculate position risk as percentage of portfolio.

        Args:
            position_size: Position size in USDC
            portfolio_value: Total portfolio value in USDC

        Returns:
            Risk value object

        Raises:
            ValueError: If position size exceeds max
        """
        if portfolio_value <= Decimal("0"):
            raise ValueError("portfolio_value must be positive")

        risk_ratio = position_size / portfolio_value

        if risk_ratio > RiskCalculator.MAX_POSITION_SIZE_PCT:
            raise ValueError(
                f"Position size {risk_ratio*100:.1f}% exceeds max "
                f"{RiskCalculator.MAX_POSITION_SIZE_PCT*100:.1f}%"
            )

        return Risk(risk_ratio)

    @staticmethod
    def validate_order(order: Order, portfolio_value: Decimal) -> bool:
        """Validate order against risk rules.

        Args:
            order: Order to validate
            portfolio_value: Total portfolio value

        Returns:
            True if order is valid

        Raises:
            ValueError: If order violates risk rules
        """
        # Zone 4-5 directional PROHIBITED
        if order.zone.is_directional_prohibited():
            raise ValueError(
                f"Zone {order.zone.value} directional trading PROHIBITED"
            )

        # Post-only OBLIGATORIO
        if not order.post_only:
            raise ValueError("post_only must be True - taker orders PROHIBITED")

        # Position size check
        position_value = order.size.value * order.price.value
        RiskCalculator.calculate_position_risk(position_value, portfolio_value)

        return True

    @staticmethod
    def calculate_drawdown(
        current_value: Decimal,
        peak_value: Decimal,
    ) -> Decimal:
        """Calculate drawdown from peak.

        Args:
            current_value: Current portfolio/bot value
            peak_value: Peak value (high water mark)

        Returns:
            Drawdown as percentage (0.0 to 1.0)
        """
        if peak_value <= Decimal("0"):
            return Decimal("0")

        if current_value >= peak_value:
            return Decimal("0")

        drawdown = (peak_value - current_value) / peak_value
        return drawdown

    @staticmethod
    def check_circuit_breaker(
        consecutive_losses: int,
        daily_loss_pct: Decimal,
        bot_drawdown_pct: Decimal,
        portfolio_drawdown_pct: Decimal,
    ) -> tuple[bool, Optional[str]]:
        """Check if circuit breaker should trigger.

        Args:
            consecutive_losses: Number of consecutive losses
            daily_loss_pct: Daily loss percentage
            bot_drawdown_pct: Bot drawdown percentage
            portfolio_drawdown_pct: Portfolio drawdown percentage

        Returns:
            Tuple of (should_stop, reason)

        Example:
            >>> should_stop, reason = calc.check_circuit_breaker(
            ...     consecutive_losses=3,
            ...     daily_loss_pct=Decimal("0.06"),
            ...     bot_drawdown_pct=Decimal("0.20"),
            ...     portfolio_drawdown_pct=Decimal("0.35"),
            ... )
            >>> should_stop
            True
            >>> reason
            '3 consecutive losses'
        """
        # 3 consecutive losses
        if consecutive_losses >= RiskCalculator.MAX_CONSECUTIVE_LOSSES:
            return True, f"{consecutive_losses} consecutive losses"

        # 5% daily loss
        if daily_loss_pct >= RiskCalculator.MAX_DAILY_LOSS_PCT:
            return True, f"Daily loss {daily_loss_pct*100:.1f}% exceeds 5%"

        # 25% bot drawdown
        if bot_drawdown_pct >= RiskCalculator.MAX_BOT_DRAWDOWN_PCT:
            return True, f"Bot drawdown {bot_drawdown_pct*100:.1f}% exceeds 25%"

        # 40% portfolio drawdown
        if portfolio_drawdown_pct >= RiskCalculator.MAX_PORTFOLIO_DRAWDOWN_PCT:
            return (
                True,
                f"Portfolio drawdown {portfolio_drawdown_pct*100:.1f}% exceeds 40%",
            )

        return False, None

    @staticmethod
    def calculate_var(
        positions: list[Position],
        confidence: Decimal = Decimal("0.95"),
    ) -> Decimal:
        """Calculate Value at Risk (simplified).

        Args:
            positions: List of open positions
            confidence: Confidence level (default 95%)

        Returns:
            VaR estimate in USDC

        Note:
            Simplified VaR using historical volatility.
            In production, use monte carlo or historical simulation.
        """
        if not positions:
            return Decimal("0")

        # Sum position values
        total_value = sum(
            pos.size.value * pos.entry_price.value for pos in positions
        )

        # Assume 20% daily volatility (Polymarket typical)
        volatility = Decimal("0.20")

        # VaR = Value * Volatility * Z-score
        # Z-score for 95% confidence ≈ 1.645
        z_score = Decimal("1.645")

        var = total_value * volatility * z_score
        return var
