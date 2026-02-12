"""Order entity."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from src.domain.value_objects.price import Price
from src.domain.value_objects.size import Size
from src.domain.value_objects.zone import Zone


class OrderSide(str, Enum):
    """Order side."""

    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    """Order status."""

    PENDING = "PENDING"  # Created, not yet submitted
    SUBMITTED = "SUBMITTED"  # Submitted to exchange
    OPEN = "OPEN"  # Active on orderbook
    FILLED = "FILLED"  # Fully filled
    PARTIALLY_FILLED = "PARTIALLY_FILLED"  # Partially filled
    CANCELLED = "CANCELLED"  # Cancelled
    REJECTED = "REJECTED"  # Rejected by exchange
    ERROR = "ERROR"  # Error


@dataclass(frozen=True)
class Order:
    """Order entity.

    Represents a limit order with post-only enforcement.

    Example:
        >>> order = Order(
        ...     order_id=uuid4(),
        ...     bot_id=1,
        ...     market_id="0x123...",
        ...     side=OrderSide.BUY,
        ...     size=Size(Decimal("1000")),
        ...     price=Price(Decimal("0.55")),
        ...     zone=Zone(2),
        ...     status=OrderStatus.PENDING,
        ...     post_only=True,
        ...     created_at=datetime.now(),
        ...     updated_at=datetime.now(),
        ... )
    """

    order_id: UUID
    bot_id: int
    market_id: str
    side: OrderSide
    size: Size
    price: Price
    zone: Zone
    status: OrderStatus
    post_only: bool
    created_at: datetime
    updated_at: datetime
    filled_size: Optional[Size] = None

    def __post_init__(self) -> None:
        """Validate order."""
        # POST-ONLY OBLIGATORIO
        if not self.post_only:
            raise ValueError("post_only must be True - taker orders PROHIBITED")

        # Zone 4-5 directional PROHIBIDO
        if self.zone.value in (4, 5):
            raise ValueError(
                f"Zone {self.zone.value} directional trading PROHIBITED"
            )

    def is_filled(self) -> bool:
        """Check if order is fully filled."""
        return self.status == OrderStatus.FILLED

    def is_active(self) -> bool:
        """Check if order is active (can be filled)."""
        return self.status in (OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED)

    def can_cancel(self) -> bool:
        """Check if order can be cancelled."""
        return self.status in (
            OrderStatus.PENDING,
            OrderStatus.SUBMITTED,
            OrderStatus.OPEN,
            OrderStatus.PARTIALLY_FILLED,
        )
