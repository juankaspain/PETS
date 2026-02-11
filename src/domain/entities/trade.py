"""Trade entity - Executed trade record."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.domain.exceptions import DomainError
from src.domain.value_objects.identifiers import OrderId
from src.domain.value_objects.price import Price
from src.domain.value_objects.quantity import Quantity


@dataclass(frozen=True)
class Trade:
    """Executed trade entity.

    Represents a single trade execution (order fill).
    Multiple trades can result from one order.

    Attributes:
        trade_id: Unique trade identifier (UUID)
        order_id: Order that generated this trade
        executed_price: Actual execution price
        executed_size: Actual execution size
        fees_paid_usdc: Trading fees paid in USDC
        slippage_bps: Slippage in basis points (0.01% = 1 bps)
        timestamp: Trade execution timestamp
        exchange_trade_id: Exchange-assigned trade ID
    """

    trade_id: UUID
    order_id: OrderId
    executed_price: Price
    executed_size: Quantity
    fees_paid_usdc: Decimal
    slippage_bps: Decimal
    timestamp: datetime
    exchange_trade_id: str

    def __post_init__(self) -> None:
        """Validate trade attributes.

        Raises:
            DomainError: If validation fails
        """
        if self.fees_paid_usdc < Decimal("0"):
            raise DomainError(f"Fees cannot be negative: {self.fees_paid_usdc}")

        if not self.exchange_trade_id.strip():
            raise DomainError("Exchange trade ID cannot be empty")

    @property
    def trade_value_usdc(self) -> Decimal:
        """Calculate trade value in USDC.

        Returns:
            Trade value (size * price) in USDC
        """
        size_decimal = Decimal(str(self.executed_size.to_float()))
        return size_decimal * self.executed_price.value

    @property
    def effective_price(self) -> Decimal:
        """Calculate effective price including fees.

        Returns:
            Effective price (price + fees per unit)
        """
        if self.executed_size.value == Decimal("0"):
            return self.executed_price.value

        fees_per_unit = self.fees_paid_usdc / self.executed_size.value
        return self.executed_price.value + fees_per_unit

    @property
    def slippage_percentage(self) -> float:
        """Convert slippage from bps to percentage.

        Returns:
            Slippage as decimal (e.g., 0.001 for 0.1%)
        """
        return float(self.slippage_bps / Decimal("10000"))

    def __str__(self) -> str:
        """String representation."""
        return (
            f"Trade {self.trade_id}: {self.executed_size} @ {self.executed_price} "
            f"(fees: {self.fees_paid_usdc:.2f} USDC, slippage: {self.slippage_bps} bps)"
        )

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"Trade(trade_id={self.trade_id}, order_id={self.order_id}, "
            f"executed_price={self.executed_price}, "
            f"executed_size={self.executed_size})"
        )
