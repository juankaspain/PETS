"""P&L value object."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class PnL:
    """P&L value object.

    Represents realized and unrealized profit/loss.

    Example:
        >>> pnl = PnL(realized=Decimal("100"), unrealized=Decimal("50"))
        >>> pnl.total()
        Decimal('150')
    """

    realized: Optional[Decimal] = None
    unrealized: Optional[Decimal] = None

    def total(self) -> Decimal:
        """Calculate total P&L.

        Returns:
            Sum of realized and unrealized
        """
        total = Decimal("0")
        if self.realized is not None:
            total += self.realized
        if self.unrealized is not None:
            total += self.unrealized
        return total

    def is_profitable(self) -> bool:
        """Check if P&L is profitable.

        Returns:
            True if total > 0
        """
        return self.total() > Decimal("0")

    def __str__(self) -> str:
        """String representation."""
        realized_str = f"R:{self.realized}" if self.realized else ""
        unrealized_str = f"U:{self.unrealized}" if self.unrealized else ""
        parts = [p for p in [realized_str, unrealized_str] if p]
        return " ".join(parts) or "$0"
