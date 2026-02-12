"""Zone classifier domain service."""

from decimal import Decimal

from src.domain.value_objects.price import Price
from src.domain.value_objects.zone import Zone


class ZoneClassifier:
    """Zone classifier for risk zone determination.

    Maps prices to risk zones:
    - Zone 1: 0.45-0.55 (market making, lowest risk)
    - Zone 2: 0.35-0.45 or 0.55-0.65 (mean reversion, low risk)
    - Zone 3: 0.25-0.35 or 0.65-0.75 (value, medium risk)
    - Zone 4: 0.15-0.25 or 0.75-0.85 (momentum, high risk) - PROHIBITED
    - Zone 5: 0.01-0.15 or 0.85-0.99 (lottery, extreme risk) - PROHIBITED

    Example:
        >>> classifier = ZoneClassifier()
        >>> zone = classifier.classify_price(Price(Decimal("0.40")))
        >>> zone.value
        2
    """

    @staticmethod
    def classify_price(price: Price) -> Zone:
        """Classify price into risk zone.

        Args:
            price: Price to classify

        Returns:
            Zone (1-5)

        Example:
            >>> ZoneClassifier.classify_price(Price(Decimal("0.50")))
            Zone(1)
            >>> ZoneClassifier.classify_price(Price(Decimal("0.20")))
            Zone(4)
        """
        p = price.value

        # Zone 1: 0.45-0.55
        if Decimal("0.45") <= p <= Decimal("0.55"):
            return Zone(1)

        # Zone 2: 0.35-0.45 or 0.55-0.65
        if Decimal("0.35") <= p < Decimal("0.45"):
            return Zone(2)
        if Decimal("0.55") < p <= Decimal("0.65"):
            return Zone(2)

        # Zone 3: 0.25-0.35 or 0.65-0.75
        if Decimal("0.25") <= p < Decimal("0.35"):
            return Zone(3)
        if Decimal("0.65") < p <= Decimal("0.75"):
            return Zone(3)

        # Zone 4: 0.15-0.25 or 0.75-0.85
        if Decimal("0.15") <= p < Decimal("0.25"):
            return Zone(4)
        if Decimal("0.75") < p <= Decimal("0.85"):
            return Zone(4)

        # Zone 5: 0.01-0.15 or 0.85-0.99
        return Zone(5)

    @staticmethod
    def get_zone_bounds(zone: Zone) -> tuple[Decimal, Decimal]:
        """Get price bounds for zone.

        Args:
            zone: Zone to get bounds for

        Returns:
            Tuple of (min_price, max_price)

        Note:
            Zone 2-5 have two ranges (low and high).
            This returns the low range.
        """
        bounds = {
            1: (Decimal("0.45"), Decimal("0.55")),
            2: (Decimal("0.35"), Decimal("0.45")),  # Low range
            3: (Decimal("0.25"), Decimal("0.35")),  # Low range
            4: (Decimal("0.15"), Decimal("0.25")),  # Low range
            5: (Decimal("0.01"), Decimal("0.15")),  # Low range
        }
        return bounds[zone.value]

    @staticmethod
    def is_near_boundary(
        price: Price,
        threshold: Decimal = Decimal("0.02"),
    ) -> bool:
        """Check if price is near zone boundary.

        Args:
            price: Price to check
            threshold: Boundary threshold (default 0.02 = 2%)

        Returns:
            True if within threshold of zone boundary

        Example:
            >>> ZoneClassifier.is_near_boundary(Price(Decimal("0.46")))
            True  # Within 2% of 0.45 boundary
        """
        boundaries = [
            Decimal("0.45"),
            Decimal("0.55"),
            Decimal("0.35"),
            Decimal("0.65"),
            Decimal("0.25"),
            Decimal("0.75"),
            Decimal("0.15"),
            Decimal("0.85"),
        ]

        for boundary in boundaries:
            if abs(price.value - boundary) <= threshold:
                return True

        return False

    @staticmethod
    def recommend_side(price: Price) -> str:
        """Recommend trade side based on price.

        Args:
            price: Current market price

        Returns:
            'BUY' for undervalued, 'SELL' for overvalued

        Logic:
        - Price < 0.50: BUY (cheap YES)
        - Price > 0.50: SELL (expensive NO)
        """
        if price.value < Decimal("0.50"):
            return "BUY"
        else:
            return "SELL"
