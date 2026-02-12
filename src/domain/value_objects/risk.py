"""Risk value object."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Risk:
    """Risk value object.

    Represents position risk as percentage of portfolio.

    Example:
        >>> risk = Risk(Decimal("0.10"))  # 10% risk
        >>> risk.percentage()
        Decimal('10.0')
    """

    value: Decimal  # 0.0 to 1.0 (0% to 100%)

    def __post_init__(self) -> None:
        """Validate risk."""
        if not (Decimal("0") <= self.value <= Decimal("1")):
            raise ValueError(
                f"Risk must be between 0.0 and 1.0, got {self.value}"
            )

    def percentage(self) -> Decimal:
        """Get risk as percentage.

        Returns:
            Risk percentage (0-100)
        """
        return self.value * Decimal("100")

    def is_acceptable(self, max_risk: Decimal = Decimal("0.25")) -> bool:
        """Check if risk is acceptable.

        Args:
            max_risk: Maximum acceptable risk (default 25%)

        Returns:
            True if risk <= max_risk
        """
        return self.value <= max_risk

    def __str__(self) -> str:
        """String representation."""
        return f"{self.percentage():.1f}%"
