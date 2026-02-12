"""Size value object."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Size:
    """Size value object.

    Represents an order or position size (non-negative).

    Example:
        >>> size = Size(Decimal("1000"))
        >>> size.value
        Decimal('1000.000000')
    """

    value: Decimal

    def __post_init__(self) -> None:
        """Validate size."""
        # Quantize to 6 decimal places (USDC precision)
        object.__setattr__(self, "value", self.value.quantize(Decimal("0.000001")))

        if self.value < Decimal("0"):
            raise ValueError(f"Size must be non-negative, got {self.value}")

    def __float__(self) -> float:
        """Convert to float."""
        return float(self.value)

    def __str__(self) -> str:
        """String representation."""
        return str(self.value)

    def __add__(self, other: "Size") -> "Size":
        """Add two sizes."""
        return Size(self.value + other.value)

    def __sub__(self, other: "Size") -> "Size":
        """Subtract two sizes."""
        return Size(self.value - other.value)
