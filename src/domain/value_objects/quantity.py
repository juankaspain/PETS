"""Quantity value object with decimal precision."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from src.domain.exceptions import InvalidOrderError


@dataclass(frozen=True)
class Quantity:
    """Immutable quantity with decimal precision.

    Quantity represents order size or position size.
    Must be positive and respect decimal places.

    Attributes:
        value: Quantity as Decimal (must be > 0)
        decimals: Number of decimal places (default 6 for USDC)
    """

    value: Decimal
    decimals: int = 6

    # Class constants
    MIN_QUANTITY: ClassVar[Decimal] = Decimal("0.000001")  # 1 micro-unit
    DEFAULT_DECIMALS: ClassVar[int] = 6  # USDC has 6 decimals

    def __post_init__(self) -> None:
        """Validate quantity.

        Raises:
            InvalidOrderError: If quantity <= 0 or invalid decimals
        """
        # Validate positive
        if self.value <= Decimal("0"):
            raise InvalidOrderError(
                f"Quantity must be positive, got {self.value}",
                min_quantity=float(self.MIN_QUANTITY),
            )

        # Validate decimals
        if self.decimals < 0 or self.decimals > 18:
            raise InvalidOrderError(
                f"Invalid decimals: {self.decimals}", valid_range="0-18"
            )

        # Validate decimal places
        if self.value != self.value.quantize(Decimal(10) ** -self.decimals):
            raise InvalidOrderError(
                f"Quantity {self.value} exceeds {self.decimals} decimal places"
            )

    @classmethod
    def from_float(cls, value: float, decimals: int = 6) -> "Quantity":
        """Create Quantity from float.

        Args:
            value: Quantity as float (must be > 0)
            decimals: Number of decimal places (default 6)

        Returns:
            Quantity instance

        Raises:
            InvalidOrderError: If value <= 0

        Example:
            >>> qty = Quantity.from_float(100.50)
            >>> qty.to_float()
            100.5
        """
        decimal_value = Decimal(str(value))  # Convert via string for precision
        # Quantize to specified decimals
        quantized = decimal_value.quantize(Decimal(10) ** -decimals)
        return cls(value=quantized, decimals=decimals)

    @classmethod
    def from_decimal(cls, value: Decimal, decimals: int = 6) -> "Quantity":
        """Create Quantity from Decimal.

        Args:
            value: Quantity as Decimal (must be > 0)
            decimals: Number of decimal places (default 6)

        Returns:
            Quantity instance

        Raises:
            InvalidOrderError: If value <= 0

        Example:
            >>> from decimal import Decimal
            >>> qty = Quantity.from_decimal(Decimal("50.123456"))
            >>> str(qty)
            '50.123456'
        """
        quantized = value.quantize(Decimal(10) ** -decimals)
        return cls(value=quantized, decimals=decimals)

    @classmethod
    def from_int(cls, value: int, decimals: int = 6) -> "Quantity":
        """Create Quantity from integer (in smallest units).

        Args:
            value: Quantity in smallest units (e.g., micro-USDC)
            decimals: Number of decimal places (default 6)

        Returns:
            Quantity instance

        Example:
            >>> qty = Quantity.from_int(100_000_000, decimals=6)  # 100 USDC
            >>> qty.to_float()
            100.0
        """
        decimal_value = Decimal(value) / (Decimal(10) ** decimals)
        return cls(value=decimal_value, decimals=decimals)

    def to_float(self) -> float:
        """Convert quantity to float.

        Returns:
            Quantity as float
        """
        return float(self.value)

    def to_int(self) -> int:
        """Convert quantity to integer (smallest units).

        Returns:
            Quantity in smallest units

        Example:
            >>> qty = Quantity.from_float(100.5, decimals=6)
            >>> qty.to_int()
            100500000
        """
        return int(self.value * (Decimal(10) ** self.decimals))

    def add(self, other: "Quantity") -> "Quantity":
        """Add two quantities.

        Args:
            other: Quantity to add

        Returns:
            New Quantity with sum

        Raises:
            InvalidOrderError: If decimals don't match
        """
        if self.decimals != other.decimals:
            raise InvalidOrderError(
                f"Cannot add quantities with different decimals: {self.decimals} != {other.decimals}"
            )
        return Quantity(value=self.value + other.value, decimals=self.decimals)

    def subtract(self, other: "Quantity") -> "Quantity":
        """Subtract quantity.

        Args:
            other: Quantity to subtract

        Returns:
            New Quantity with difference

        Raises:
            InvalidOrderError: If decimals don't match or result negative
        """
        if self.decimals != other.decimals:
            raise InvalidOrderError(
                f"Cannot subtract quantities with different decimals: {self.decimals} != {other.decimals}"
            )
        result = self.value - other.value
        if result <= Decimal("0"):
            raise InvalidOrderError(
                f"Subtraction would result in non-positive quantity: {result}"
            )
        return Quantity(value=result, decimals=self.decimals)

    def multiply(self, scalar: Decimal) -> "Quantity":
        """Multiply quantity by scalar.

        Args:
            scalar: Decimal scalar

        Returns:
            New Quantity with product

        Raises:
            InvalidOrderError: If result would be negative
        """
        result = self.value * scalar
        if result <= Decimal("0"):
            raise InvalidOrderError(
                f"Multiplication would result in non-positive quantity: {result}"
            )
        quantized = result.quantize(Decimal(10) ** -self.decimals)
        return Quantity(value=quantized, decimals=self.decimals)

    def __str__(self) -> str:
        """String representation."""
        return str(self.value)

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Quantity(value={self.value}, decimals={self.decimals})"

    def __lt__(self, other: object) -> bool:
        """Less than comparison."""
        if not isinstance(other, Quantity):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: object) -> bool:
        """Less than or equal comparison."""
        if not isinstance(other, Quantity):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: object) -> bool:
        """Greater than comparison."""
        if not isinstance(other, Quantity):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: object) -> bool:
        """Greater than or equal comparison."""
        if not isinstance(other, Quantity):
            return NotImplemented
        return self.value >= other.value
