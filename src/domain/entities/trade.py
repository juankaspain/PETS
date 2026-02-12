"""Trade entity - executed order."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.domain.value_objects.price import Price
from src.domain.value_objects.size import Size


@dataclass(frozen=True)
class Trade:
    """Trade entity.

    Represents an executed trade with fees, slippage, and gas costs.

    Example:
        >>> trade = Trade(
        ...     trade_id=uuid4(),
        ...     order_id=order_id,
        ...     executed_price=Price(Decimal("0.55")),
        ...     executed_size=Size(Decimal("1000")),
        ...     fees_paid=Decimal("5.0"),
        ...     slippage=Decimal("0.0"),  # Post-only = no slippage
        ...     gas_cost_usdc=Decimal("0.5"),
        ...     executed_at=datetime.now(),
        ... )
    """

    trade_id: UUID
    order_id: UUID
    executed_price: Price
    executed_size: Size
    fees_paid: Decimal
    slippage: Decimal
    gas_cost_usdc: Decimal
    executed_at: datetime

    def __post_init__(self) -> None:
        """Validate trade."""
        if self.fees_paid < Decimal("0"):
            raise ValueError("fees_paid must be non-negative")

        if self.gas_cost_usdc < Decimal("0"):
            raise ValueError("gas_cost_usdc must be non-negative")

        # Post-only orders should have zero slippage
        if self.slippage != Decimal("0"):
            raise ValueError("slippage must be 0 for post-only orders")

    def total_cost(self) -> Decimal:
        """Calculate total trade cost (notional + fees + gas).

        Returns:
            Total cost in USDC
        """
        notional = self.executed_price.value * self.executed_size.value
        return notional + self.fees_paid + self.gas_cost_usdc

    def effective_price(self) -> Decimal:
        """Calculate effective price including fees.

        Returns:
            Effective price per unit
        """
        total = self.total_cost()
        return total / self.executed_size.value
