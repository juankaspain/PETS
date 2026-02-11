"""Price value object with zone auto-classification."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from src.domain.exceptions import InvalidOrderError
from src.domain.value_objects.enums import Zone


@dataclass(frozen=True)
class Price:
    """Immutable price with automatic zone classification.

    Price is always between 0.01 and 0.99 (Polymarket probability range).
    Zone is automatically assigned based on price value.

    Attributes:
        value: Price as Decimal (0.01 to 0.99)
        zone: Risk zone (1-5) based on price
    """

    value: Decimal
    zone: Zone

    # Class constants
    MIN_PRICE: ClassVar[Decimal] = Decimal("0.01")
    MAX_PRICE: ClassVar[Decimal] = Decimal("0.99")

    def __post_init__(self) -> None:
        """Validate price range and zone classification.

        Raises:
            InvalidOrderError: If price out of range or zone mismatch
        """
        # Validate price range
        if not (self.MIN_PRICE <= self.value <= self.MAX_PRICE):
            raise InvalidOrderError(
                f"Price {self.value} out of valid range",
                min_price=float(self.MIN_PRICE),
                max_price=float(self.MAX_PRICE),
            )

        # Validate zone matches price
        expected_zone = self._classify_zone(self.value)
        if self.zone != expected_zone:
            raise InvalidOrderError(
                f"Zone {self.zone} doesn't match price {self.value}",
                expected_zone=expected_zone,
            )

    @classmethod
    def from_float(cls, value: float) -> "Price":
        """Create Price from float.

        Args:
            value: Price as float (0.01 to 0.99)

        Returns:
            Price instance with auto-classified zone

        Raises:
            InvalidOrderError: If value out of range

        Example:
            >>> price = Price.from_float(0.15)
            >>> price.zone
            Zone.ZONE_1
        """
        decimal_value = Decimal(str(value))  # Convert via string for precision
        zone = cls._classify_zone(decimal_value)
        return cls(value=decimal_value, zone=zone)

    @classmethod
    def from_decimal(cls, value: Decimal) -> "Price":
        """Create Price from Decimal.

        Args:
            value: Price as Decimal (0.01 to 0.99)

        Returns:
            Price instance with auto-classified zone

        Raises:
            InvalidOrderError: If value out of range

        Example:
            >>> from decimal import Decimal
            >>> price = Price.from_decimal(Decimal("0.75"))
            >>> price.zone
            Zone.ZONE_4
        """
        zone = cls._classify_zone(value)
        return cls(value=value, zone=zone)

    @staticmethod
    def _classify_zone(value: Decimal) -> Zone:
        """Classify price into zone.

        Args:
            value: Price value

        Returns:
            Zone enum (ZONE_1 to ZONE_5)

        Zone boundaries:
        - Zone 1: 0.05 - 0.20
        - Zone 2: 0.20 - 0.40
        - Zone 3: 0.40 - 0.60
        - Zone 4: 0.60 - 0.80
        - Zone 5: 0.80 - 0.98
        """
        if value < Decimal("0.20"):
            return Zone.ZONE_1
        if value < Decimal("0.40"):
            return Zone.ZONE_2
        if value < Decimal("0.60"):
            return Zone.ZONE_3
        if value < Decimal("0.80"):
            return Zone.ZONE_4
        return Zone.ZONE_5

    def to_float(self) -> float:
        """Convert price to float.

        Returns:
            Price as float
        """
        return float(self.value)

    def complement(self) -> "Price":
        """Get complement price (1 - price).

        Returns:
            Complement price (for opposite side)

        Example:
            >>> price = Price.from_float(0.30)
            >>> complement = price.complement()
            >>> complement.to_float()
            0.70
        """
        complement_value = Decimal("1.00") - self.value
        return Price.from_decimal(complement_value)

    def __str__(self) -> str:
        """String representation."""
        return f"{self.value} (Zone {self.zone.value})"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Price(value={self.value}, zone={self.zone})"

    def __lt__(self, other: object) -> bool:
        """Less than comparison."""
        if not isinstance(other, Price):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: object) -> bool:
        """Less than or equal comparison."""
        if not isinstance(other, Price):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: object) -> bool:
        """Greater than comparison."""
        if not isinstance(other, Price):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: object) -> bool:
        """Greater than or equal comparison."""
        if not isinstance(other, Price):
            return NotImplemented
        return self.value >= other.value
