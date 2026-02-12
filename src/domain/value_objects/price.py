"""Price value object."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Price:
    """Price value object.

    Represents a price in Polymarket (0.01 to 0.99).

    Example:
        >>> price = Price(Decimal("0.55"))
        >>> price.value
        Decimal('0.5500')
    """

    value: Decimal

    def __post_init__(self) -> None:
        """Validate price."""
        # Quantize to 4 decimal places (0.0001 precision)
        object.__setattr__(self, "value", self.value.quantize(Decimal("0.0001")))

        # Polymarket price bounds
        if not (Decimal("0.01") <= self.value <= Decimal("0.99")):
            raise ValueError(
                f"Price must be between 0.01 and 0.99, got {self.value}"
            )

    def __float__(self) -> float:
        """Convert to float."""
        return float(self.value)

    def __str__(self) -> str:
        """String representation."""
        return str(self.value)
