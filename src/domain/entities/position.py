"""Position entity with P&L tracking."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from src.domain.entities.order import OrderSide
from src.domain.value_objects.price import Price
from src.domain.value_objects.pnl import PnL
from src.domain.value_objects.size import Size
from src.domain.value_objects.zone import Zone


@dataclass(frozen=True)
class Position:
    """Position entity.

    Represents an open or closed trading position with P&L tracking.

    Example:
        >>> position = Position(
        ...     position_id=uuid4(),
        ...     bot_id=1,
        ...     order_id=order_id,
        ...     market_id="0x123...",
        ...     side=OrderSide.BUY,
        ...     size=Size(Decimal("1000")),
        ...     entry_price=Price(Decimal("0.55")),
        ...     zone=Zone(2),
        ...     opened_at=datetime.now(),
        ... )
    """

    position_id: UUID
    bot_id: int
    order_id: UUID
    market_id: str
    side: OrderSide
    size: Size
    entry_price: Price
    zone: Zone
    opened_at: datetime
    current_price: Optional[Price] = None
    pnl: Optional[PnL] = None
    closed_at: Optional[datetime] = None

    def is_open(self) -> bool:
        """Check if position is open."""
        return self.closed_at is None

    def calculate_unrealized_pnl(self, current_price: Price) -> PnL:
        """Calculate unrealized P&L.

        Args:
            current_price: Current market price

        Returns:
            PnL with unrealized value

        Formula:
        - BUY: (current_price - entry_price) * size
        - SELL: (entry_price - current_price) * size
        """
        if not self.is_open():
            raise ValueError("Position is closed")

        if self.side == OrderSide.BUY:
            pnl_value = (current_price.value - self.entry_price.value) * self.size.value
        else:
            pnl_value = (self.entry_price.value - current_price.value) * self.size.value

        return PnL(realized=None, unrealized=pnl_value)

    def holding_time_hours(self) -> float:
        """Calculate holding time in hours."""
        end_time = self.closed_at or datetime.now()
        delta = end_time - self.opened_at
        return delta.total_seconds() / 3600
