"""Market entity - Prediction market representation."""

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal

from src.domain.exceptions import DomainError
from src.domain.value_objects.identifiers import MarketId


@dataclass(frozen=True)
class Market:
    """Prediction market entity.

    Represents a binary prediction market on Polymarket.

    Attributes:
        market_id: Unique market identifier (hex format)
        question: Market question text
        outcomes: List of outcome names (usually ["Yes", "No"])
        liquidity_usdc: Current liquidity in USDC
        volume_24h_usdc: 24h trading volume in USDC
        created_at: Market creation timestamp
        resolves_at: Expected resolution timestamp
        resolved_at: Actual resolution timestamp (None if not resolved)
        winning_outcome: Winning outcome index (None if not resolved)
    """

    market_id: MarketId
    question: str
    outcomes: tuple[str, ...]
    liquidity_usdc: Decimal
    volume_24h_usdc: Decimal
    created_at: datetime
    resolves_at: datetime
    resolved_at: datetime | None = None
    winning_outcome: int | None = None

    def __post_init__(self) -> None:
        """Validate market attributes.

        Raises:
            DomainError: If validation fails
        """
        if not self.question.strip():
            raise DomainError("Market question cannot be empty")

        if len(self.outcomes) < 2:
            raise DomainError(
                f"Market must have at least 2 outcomes, got {len(self.outcomes)}"
            )

        if self.liquidity_usdc < Decimal("0"):
            raise DomainError(f"Liquidity cannot be negative: {self.liquidity_usdc}")

        if self.volume_24h_usdc < Decimal("0"):
            raise DomainError(
                f"Volume cannot be negative: {self.volume_24h_usdc}"
            )

        if self.resolved_at is not None and self.winning_outcome is None:
            raise DomainError(
                "Resolved market must have winning_outcome",
                market_id=str(self.market_id),
            )

        if self.winning_outcome is not None:
            if not 0 <= self.winning_outcome < len(self.outcomes):
                raise DomainError(
                    f"Invalid winning_outcome: {self.winning_outcome}",
                    valid_range=f"0-{len(self.outcomes)-1}",
                )

    def update_liquidity(self, new_liquidity: Decimal) -> "Market":
        """Update market liquidity.

        Args:
            new_liquidity: New liquidity value in USDC

        Returns:
            New Market instance with updated liquidity

        Raises:
            DomainError: If new_liquidity negative
        """
        if new_liquidity < Decimal("0"):
            raise DomainError(f"Liquidity cannot be negative: {new_liquidity}")

        return replace(self, liquidity_usdc=new_liquidity)

    def update_volume(self, new_volume: Decimal) -> "Market":
        """Update 24h trading volume.

        Args:
            new_volume: New 24h volume in USDC

        Returns:
            New Market instance with updated volume

        Raises:
            DomainError: If new_volume negative
        """
        if new_volume < Decimal("0"):
            raise DomainError(f"Volume cannot be negative: {new_volume}")

        return replace(self, volume_24h_usdc=new_volume)

    def resolve(self, winning_outcome: int, timestamp: datetime) -> "Market":
        """Resolve market with winning outcome.

        Args:
            winning_outcome: Index of winning outcome
            timestamp: Resolution timestamp

        Returns:
            New Market instance with resolution data

        Raises:
            DomainError: If already resolved or invalid outcome
        """
        if self.is_resolved:
            raise DomainError(
                "Market already resolved", market_id=str(self.market_id)
            )

        if not 0 <= winning_outcome < len(self.outcomes):
            raise DomainError(
                f"Invalid winning_outcome: {winning_outcome}",
                valid_range=f"0-{len(self.outcomes)-1}",
            )

        return replace(
            self, resolved_at=timestamp, winning_outcome=winning_outcome
        )

    @property
    def is_resolved(self) -> bool:
        """Check if market is resolved."""
        return self.resolved_at is not None

    @property
    def is_expired(self) -> bool:
        """Check if market has passed resolution date."""
        return datetime.utcnow() > self.resolves_at

    @property
    def days_until_resolution(self) -> float:
        """Get days until expected resolution.

        Returns:
            Days until resolution (negative if expired)
        """
        delta = self.resolves_at - datetime.utcnow()
        return delta.total_seconds() / 86400  # seconds per day

    def __str__(self) -> str:
        """String representation."""
        status = "RESOLVED" if self.is_resolved else "ACTIVE"
        return f"Market {self.market_id}: {self.question[:50]}... ({status})"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"Market(market_id={self.market_id}, "
            f"question='{self.question[:30]}...', "
            f"is_resolved={self.is_resolved})"
        )
