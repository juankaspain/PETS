"""Position entity - P&L tracking and lifecycle."""

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.domain.exceptions import DomainError, PositionAlreadyClosedError
from src.domain.value_objects.enums import Side, Zone
from src.domain.value_objects.identifiers import MarketId, OrderId
from src.domain.value_objects.price import Price
from src.domain.value_objects.quantity import Quantity


@dataclass(frozen=True)
class Position:
    """Position entity with P&L tracking.

    Represents an open or closed trading position.
    Tracks entry, current price, and realized/unrealized P&L.

    Attributes:
        position_id: Unique position identifier (UUID)
        bot_id: Bot that opened this position
        order_id: Order that opened this position
        market_id: Market identifier
        side: Position side (YES or NO)
        size: Position size
        entry_price: Entry price
        current_price: Current market price (updated)
        zone: Risk zone at entry
        opened_at: Position open timestamp
        closed_at: Position close timestamp (None if open)
        exit_price: Exit price (None if open)
        realized_pnl: Realized P&L in USDC (None if open)
    """

    position_id: UUID
    bot_id: int
    order_id: OrderId
    market_id: MarketId
    side: Side
    size: Quantity
    entry_price: Price
    current_price: Price
    zone: Zone
    opened_at: datetime
    closed_at: datetime | None = None
    exit_price: Price | None = None
    realized_pnl: Decimal | None = None

    def __post_init__(self) -> None:
        """Validate position attributes.

        Raises:
            DomainError: If validation fails
        """
        if not 1 <= self.bot_id <= 10:
            raise DomainError(f"Invalid bot_id: {self.bot_id}", valid_range="1-10")

        if self.closed_at is not None:
            if self.exit_price is None or self.realized_pnl is None:
                raise DomainError(
                    "Closed position must have exit_price and realized_pnl",
                    position_id=str(self.position_id),
                )

    def update_current_price(self, new_price: Price) -> "Position":
        """Update current market price.

        Args:
            new_price: New market price

        Returns:
            New Position instance with updated current_price

        Raises:
            PositionAlreadyClosedError: If position is closed
        """
        if self.is_closed:
            raise PositionAlreadyClosedError(
                "Cannot update price on closed position",
                position_id=str(self.position_id),
            )

        return replace(self, current_price=new_price)

    def close(
        self, exit_price: Price, timestamp: datetime, fees: Decimal = Decimal("0")
    ) -> "Position":
        """Close position and calculate realized P&L.

        Args:
            exit_price: Exit price
            timestamp: Close timestamp
            fees: Total fees paid (entry + exit)

        Returns:
            New Position instance with closed status and realized P&L

        Raises:
            PositionAlreadyClosedError: If position already closed
        """
        if self.is_closed:
            raise PositionAlreadyClosedError(
                "Position already closed", position_id=str(self.position_id)
            )

        # Calculate P&L
        # For YES positions: profit if price increases
        # For NO positions: profit if price decreases
        size_value = Decimal(str(self.size.to_float()))
        price_diff = exit_price.value - self.entry_price.value

        if self.side == Side.YES:
            gross_pnl = size_value * price_diff
        else:  # Side.NO
            gross_pnl = size_value * (-price_diff)

        net_pnl = gross_pnl - fees

        return replace(
            self,
            closed_at=timestamp,
            exit_price=exit_price,
            current_price=exit_price,
            realized_pnl=net_pnl,
        )

    @property
    def is_closed(self) -> bool:
        """Check if position is closed."""
        return self.closed_at is not None

    @property
    def unrealized_pnl(self) -> Decimal:
        """Calculate unrealized P&L based on current price.

        Returns:
            Unrealized P&L in USDC (0 if closed)
        """
        if self.is_closed:
            return Decimal("0")

        size_value = Decimal(str(self.size.to_float()))
        price_diff = self.current_price.value - self.entry_price.value

        if self.side == Side.YES:
            return size_value * price_diff
        else:  # Side.NO
            return size_value * (-price_diff)

    @property
    def hold_duration_seconds(self) -> float:
        """Get position hold duration in seconds.

        Returns:
            Duration in seconds (0 if not closed)
        """
        if not self.is_closed:
            return 0.0

        assert self.closed_at is not None  # For type checker
        return (self.closed_at - self.opened_at).total_seconds()

    @property
    def return_percentage(self) -> float:
        """Calculate return percentage.

        Returns:
            Return as percentage (e.g., 0.05 for 5% gain)
        """
        if not self.is_closed or self.realized_pnl is None:
            # Use unrealized P&L
            pnl = self.unrealized_pnl
        else:
            pnl = self.realized_pnl

        cost_basis = Decimal(str(self.size.to_float())) * self.entry_price.value
        if cost_basis == Decimal("0"):
            return 0.0

        return float(pnl / cost_basis)

    def __str__(self) -> str:
        """String representation."""
        status = "CLOSED" if self.is_closed else "OPEN"
        pnl_str = (
            f"P&L: {self.realized_pnl:.2f} USDC"
            if self.is_closed
            else f"Unrealized P&L: {self.unrealized_pnl:.2f} USDC"
        )
        return (
            f"Position {self.position_id}: {self.side.value} {self.size} @ "
            f"{self.entry_price} ({status}, {pnl_str})"
        )

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"Position(position_id={self.position_id}, bot_id={self.bot_id}, "
            f"market={self.market_id}, side={self.side}, "
            f"is_closed={self.is_closed})"
        )
