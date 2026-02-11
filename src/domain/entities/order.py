"""Order entity - Order lifecycle tracking."""

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.domain.exceptions import DomainError, InvalidOrderError
from src.domain.value_objects.enums import OrderStatus, Side, Zone
from src.domain.value_objects.identifiers import MarketId, OrderId
from src.domain.value_objects.price import Price
from src.domain.value_objects.quantity import Quantity


@dataclass(frozen=True)
class Order:
    """Order entity with lifecycle tracking.

    Represents a single order through its lifecycle from creation to terminal state.

    Attributes:
        order_id: Unique order identifier (UUID)
        bot_id: Bot that created this order
        market_id: Market identifier
        side: Order side (YES or NO)
        size: Order size
        price: Order price with zone
        status: Current order status
        post_only: If True, order is maker-only (no taker fees)
        created_at: Order creation timestamp
        submitted_at: Exchange submission timestamp
        updated_at: Last status update timestamp
        filled_size: Amount filled (for partial fills)
        average_fill_price: Average price of fills (None if not filled)
        exchange_order_id: Exchange-assigned order ID (None if not submitted)
    """

    order_id: OrderId
    bot_id: int
    market_id: MarketId
    side: Side
    size: Quantity
    price: Price
    status: OrderStatus
    post_only: bool
    created_at: datetime
    submitted_at: datetime | None = None
    updated_at: datetime | None = None
    filled_size: Quantity | None = None
    average_fill_price: Price | None = None
    exchange_order_id: str | None = None

    def __post_init__(self) -> None:
        """Validate order attributes.

        Raises:
            InvalidOrderError: If validation fails
        """
        if not 1 <= self.bot_id <= 10:
            raise InvalidOrderError(
                f"Invalid bot_id: {self.bot_id}", valid_range="1-10"
            )

        if self.filled_size is not None:
            if self.filled_size > self.size:
                raise InvalidOrderError(
                    f"Filled size {self.filled_size} exceeds order size {self.size}"
                )

        if self.status.is_terminal and self.updated_at is None:
            raise InvalidOrderError(
                f"Terminal status {self.status} requires updated_at"
            )

    def submit(self, timestamp: datetime, exchange_order_id: str) -> "Order":
        """Mark order as submitted to exchange.

        Args:
            timestamp: Submission timestamp
            exchange_order_id: Exchange-assigned order ID

        Returns:
            New Order instance with SUBMITTED status

        Raises:
            DomainError: If order not in PENDING status
        """
        if self.status != OrderStatus.PENDING:
            raise DomainError(
                f"Can only submit PENDING orders, current: {self.status}",
                order_id=str(self.order_id),
            )

        return replace(
            self,
            status=OrderStatus.SUBMITTED,
            submitted_at=timestamp,
            updated_at=timestamp,
            exchange_order_id=exchange_order_id,
        )

    def mark_open(self, timestamp: datetime) -> "Order":
        """Mark order as open on exchange.

        Args:
            timestamp: Open timestamp

        Returns:
            New Order instance with OPEN status

        Raises:
            DomainError: If order not in SUBMITTED status
        """
        if self.status != OrderStatus.SUBMITTED:
            raise DomainError(
                f"Can only open SUBMITTED orders, current: {self.status}",
                order_id=str(self.order_id),
            )

        return replace(self, status=OrderStatus.OPEN, updated_at=timestamp)

    def partial_fill(
        self, filled_size: Quantity, fill_price: Price, timestamp: datetime
    ) -> "Order":
        """Record partial fill.

        Args:
            filled_size: Additional size filled
            fill_price: Fill price
            timestamp: Fill timestamp

        Returns:
            New Order instance with updated filled_size and PARTIALLY_FILLED status

        Raises:
            DomainError: If order not active or fill exceeds remaining size
        """
        if not self.status.is_active:
            raise DomainError(
                f"Cannot fill non-active order, current: {self.status}",
                order_id=str(self.order_id),
            )

        current_filled = self.filled_size or Quantity.from_float(0.0)
        new_filled = current_filled.add(filled_size)

        if new_filled > self.size:
            raise DomainError(
                f"Fill would exceed order size: {new_filled} > {self.size}",
                order_id=str(self.order_id),
            )

        # Calculate new average fill price
        if self.average_fill_price is None:
            new_avg_price = fill_price
        else:
            # Weighted average
            current_value = Decimal(str(current_filled.to_float())) * self.average_fill_price.value
            new_value = Decimal(str(filled_size.to_float())) * fill_price.value
            total_value = current_value + new_value
            avg_price_value = total_value / Decimal(str(new_filled.to_float()))
            new_avg_price = Price.from_decimal(avg_price_value)

        return replace(
            self,
            status=OrderStatus.PARTIALLY_FILLED,
            filled_size=new_filled,
            average_fill_price=new_avg_price,
            updated_at=timestamp,
        )

    def complete_fill(
        self, fill_price: Price, timestamp: datetime
    ) -> "Order":
        """Mark order as completely filled.

        Args:
            fill_price: Final fill price
            timestamp: Fill timestamp

        Returns:
            New Order instance with FILLED status

        Raises:
            DomainError: If order not active
        """
        if not self.status.is_active:
            raise DomainError(
                f"Cannot fill non-active order, current: {self.status}",
                order_id=str(self.order_id),
            )

        # Calculate final average price
        if self.filled_size is None:
            # Fully filled in one go
            new_avg_price = fill_price
            new_filled = self.size
        else:
            # Complete partial fill
            remaining = self.size.subtract(self.filled_size)
            current_value = Decimal(str(self.filled_size.to_float())) * self.average_fill_price.value
            remaining_value = Decimal(str(remaining.to_float())) * fill_price.value
            total_value = current_value + remaining_value
            avg_price_value = total_value / Decimal(str(self.size.to_float()))
            new_avg_price = Price.from_decimal(avg_price_value)
            new_filled = self.size

        return replace(
            self,
            status=OrderStatus.FILLED,
            filled_size=new_filled,
            average_fill_price=new_avg_price,
            updated_at=timestamp,
        )

    def cancel(self, timestamp: datetime) -> "Order":
        """Cancel order.

        Args:
            timestamp: Cancellation timestamp

        Returns:
            New Order instance with CANCELED status

        Raises:
            DomainError: If order already in terminal state
        """
        if self.status.is_terminal:
            raise DomainError(
                f"Cannot cancel order in terminal state: {self.status}",
                order_id=str(self.order_id),
            )

        return replace(self, status=OrderStatus.CANCELED, updated_at=timestamp)

    def reject(self, timestamp: datetime, reason: str) -> "Order":
        """Mark order as rejected.

        Args:
            timestamp: Rejection timestamp
            reason: Rejection reason

        Returns:
            New Order instance with REJECTED status
        """
        return replace(self, status=OrderStatus.REJECTED, updated_at=timestamp)

    def expire(self, timestamp: datetime) -> "Order":
        """Mark order as expired.

        Args:
            timestamp: Expiration timestamp

        Returns:
            New Order instance with EXPIRED status
        """
        return replace(self, status=OrderStatus.EXPIRED, updated_at=timestamp)

    @property
    def is_terminal(self) -> bool:
        """Check if order is in terminal state."""
        return self.status.is_terminal

    @property
    def is_active(self) -> bool:
        """Check if order is active on exchange."""
        return self.status.is_active

    @property
    def remaining_size(self) -> Quantity:
        """Get remaining unfilled size."""
        if self.filled_size is None:
            return self.size
        return self.size.subtract(self.filled_size)

    @property
    def fill_percentage(self) -> float:
        """Get fill percentage (0.0 to 1.0)."""
        if self.filled_size is None:
            return 0.0
        return self.filled_size.to_float() / self.size.to_float()

    def __str__(self) -> str:
        """String representation."""
        return (
            f"Order {self.order_id}: {self.side.value} {self.size} @ {self.price} "
            f"({self.status.value})"
        )

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"Order(order_id={self.order_id}, bot_id={self.bot_id}, "
            f"market={self.market_id}, status={self.status})"
        )
