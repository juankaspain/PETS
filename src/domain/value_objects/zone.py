"""Zone value object for risk classification."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Zone:
    """Zone value object.

    Represents risk zones 1-5:
    - Zone 1: 0.45-0.55 (lowest risk, market making)
    - Zone 2: 0.35-0.45 or 0.55-0.65 (low risk, mean reversion)
    - Zone 3: 0.25-0.35 or 0.65-0.75 (medium risk, value)
    - Zone 4: 0.15-0.25 or 0.75-0.85 (high risk, momentum) - PROHIBIDO directional
    - Zone 5: 0.01-0.15 or 0.85-0.99 (extreme risk, lottery) - PROHIBIDO directional

    Example:
        >>> zone = Zone(2)
        >>> zone.value
        2
        >>> zone.is_safe()
        True
    """

    value: int

    def __post_init__(self) -> None:
        """Validate zone."""
        if not (1 <= self.value <= 5):
            raise ValueError(f"Zone must be 1-5, got {self.value}")

    def is_safe(self) -> bool:
        """Check if zone is safe for trading.

        Returns:
            True if zone 1-3
        """
        return self.value <= 3

    def is_directional_prohibited(self) -> bool:
        """Check if directional trading is prohibited in this zone.

        Returns:
            True if zone 4-5
        """
        return self.value >= 4

    def max_kelly_fraction(self) -> float:
        """Get max Kelly fraction for zone.

        Returns:
            Max Kelly fraction (0.0-0.5)
        """
        # Zone 1: 50% (Half Kelly)
        # Zone 2: 50% (Half Kelly)
        # Zone 3: 25% (Quarter Kelly)
        # Zone 4-5: 0% (PROHIBITED directional)
        if self.value == 1:
            return 0.5
        elif self.value == 2:
            return 0.5
        elif self.value == 3:
            return 0.25
        else:
            return 0.0

    def __str__(self) -> str:
        """String representation."""
        return f"Z{self.value}"
