"""Market entity."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from src.domain.value_objects.price import Price


@dataclass(frozen=True)
class Market:
    """Market entity.

    Represents a prediction market with question, outcomes, and pricing.

    Example:
        >>> market = Market(
        ...     market_id="0x123...",
        ...     question="Will X happen?",
        ...     outcomes=["YES", "NO"],
        ...     liquidity=Decimal("100000"),
        ...     volume_24h=Decimal("50000"),
        ...     yes_price=Price(Decimal("0.55")),
        ...     no_price=Price(Decimal("0.45")),
        ...     created_at=datetime.now(),
        ... )
    """

    market_id: str
    question: str
    outcomes: list[str]
    liquidity: Decimal
    volume_24h: Decimal
    created_at: datetime
    updated_at: datetime
    yes_price: Optional[Price] = None
    no_price: Optional[Price] = None
    resolves_at: Optional[datetime] = None
    resolved: bool = False
    resolved_outcome: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate market."""
        if self.liquidity < Decimal("0"):
            raise ValueError("liquidity must be non-negative")

        if self.volume_24h < Decimal("0"):
            raise ValueError("volume_24h must be non-negative")

        if not self.outcomes:
            raise ValueError("outcomes cannot be empty")

        # Validate prices sum to ~1.0 (allowing small rounding)
        if self.yes_price and self.no_price:
            price_sum = self.yes_price.value + self.no_price.value
            if abs(price_sum - Decimal("1.0")) > Decimal("0.01"):
                raise ValueError(
                    f"YES + NO prices must sum to ~1.0, got {price_sum}"
                )

    def is_active(self) -> bool:
        """Check if market is active (not resolved)."""
        return not self.resolved

    def has_sufficient_liquidity(self, min_liquidity: Decimal) -> bool:
        """Check if market has sufficient liquidity.

        Args:
            min_liquidity: Minimum required liquidity

        Returns:
            True if liquidity >= min_liquidity
        """
        return self.liquidity >= min_liquidity

    def spread(self) -> Optional[Decimal]:
        """Calculate bid-ask spread.

        Returns:
            Spread or None if prices not available
        """
        if self.yes_price and self.no_price:
            # In Polymarket, spread is implicit in YES/NO pricing
            # Simple spread: deviation from 0.5
            return abs(self.yes_price.value - Decimal("0.5")) * Decimal("2")
        return None
