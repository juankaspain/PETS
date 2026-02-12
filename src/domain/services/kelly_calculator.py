"""Kelly calculator domain service."""

from decimal import Decimal

from src.domain.value_objects.zone import Zone


class KellyCalculator:
    """Kelly calculator for optimal position sizing.

    Implements Half Kelly and Quarter Kelly (NEVER Full Kelly).

    Kelly formula: f* = (p * b - q) / b
    Where:
    - p = win probability
    - q = loss probability (1 - p)
    - b = odds (win_amount / loss_amount)

    Example:
        >>> calc = KellyCalculator()
        >>> fraction = calc.calculate_half_kelly(
        ...     win_prob=Decimal("0.60"),
        ...     edge=Decimal("0.15"),
        ... )
        >>> fraction
        Decimal('0.15')  # 15% of portfolio
    """

    # Minimum edge required (5%)
    MIN_EDGE = Decimal("0.05")

    @staticmethod
    def calculate_full_kelly(
        win_prob: Decimal,
        edge: Decimal,
    ) -> Decimal:
        """Calculate Full Kelly fraction.

        WARNING: NEVER use Full Kelly in production.
        This method is for reference only.

        Args:
            win_prob: Win probability (0.0 to 1.0)
            edge: Expected edge (e.g., 0.15 for 15%)

        Returns:
            Kelly fraction (0.0 to 1.0)
        """
        if not (Decimal("0") < win_prob < Decimal("1")):
            raise ValueError("win_prob must be between 0 and 1")

        if edge < KellyCalculator.MIN_EDGE:
            return Decimal("0")  # No edge, no bet

        loss_prob = Decimal("1") - win_prob

        # Kelly formula: f* = (p * b - q) / b
        # For binary outcome: b = (1 + edge) / 1 = 1 + edge
        # Simplified: f* = p - q / (1 + edge)
        numerator = win_prob * (Decimal("1") + edge) - loss_prob
        denominator = Decimal("1") + edge

        kelly = numerator / denominator

        # Clip to [0, 1]
        return max(Decimal("0"), min(Decimal("1"), kelly))

    @staticmethod
    def calculate_half_kelly(
        win_prob: Decimal,
        edge: Decimal,
    ) -> Decimal:
        """Calculate Half Kelly fraction.

        Half Kelly = Full Kelly / 2
        Reduces variance while maintaining most of growth rate.

        Args:
            win_prob: Win probability (0.0 to 1.0)
            edge: Expected edge

        Returns:
            Half Kelly fraction (0.0 to 0.5)
        """
        full_kelly = KellyCalculator.calculate_full_kelly(win_prob, edge)
        return full_kelly / Decimal("2")

    @staticmethod
    def calculate_quarter_kelly(
        win_prob: Decimal,
        edge: Decimal,
    ) -> Decimal:
        """Calculate Quarter Kelly fraction.

        Quarter Kelly = Full Kelly / 4
        Even more conservative for high-risk zones.

        Args:
            win_prob: Win probability (0.0 to 1.0)
            edge: Expected edge

        Returns:
            Quarter Kelly fraction (0.0 to 0.25)
        """
        full_kelly = KellyCalculator.calculate_full_kelly(win_prob, edge)
        return full_kelly / Decimal("4")

    @staticmethod
    def calculate_for_zone(
        zone: Zone,
        win_prob: Decimal,
        edge: Decimal,
    ) -> Decimal:
        """Calculate Kelly fraction for specific zone.

        Zone 1-2: Half Kelly (max 50%)
        Zone 3: Quarter Kelly (max 25%)
        Zone 4-5: 0% (PROHIBITED)

        Args:
            zone: Risk zone
            win_prob: Win probability
            edge: Expected edge

        Returns:
            Kelly fraction appropriate for zone
        """
        if zone.is_directional_prohibited():
            return Decimal("0")  # Zone 4-5 PROHIBITED

        if zone.value <= 2:
            # Zone 1-2: Half Kelly
            kelly = KellyCalculator.calculate_half_kelly(win_prob, edge)
            max_fraction = Decimal("0.50")
        else:
            # Zone 3: Quarter Kelly
            kelly = KellyCalculator.calculate_quarter_kelly(win_prob, edge)
            max_fraction = Decimal("0.25")

        # Apply zone max
        return min(kelly, max_fraction)

    @staticmethod
    def calculate_position_size(
        zone: Zone,
        win_prob: Decimal,
        edge: Decimal,
        portfolio_value: Decimal,
    ) -> Decimal:
        """Calculate position size in USDC.

        Args:
            zone: Risk zone
            win_prob: Win probability
            edge: Expected edge
            portfolio_value: Total portfolio value

        Returns:
            Position size in USDC

        Example:
            >>> size = calc.calculate_position_size(
            ...     zone=Zone(2),
            ...     win_prob=Decimal("0.60"),
            ...     edge=Decimal("0.15"),
            ...     portfolio_value=Decimal("10000"),
            ... )
            >>> size
            Decimal('1500.00')  # 15% of $10K
        """
        kelly_fraction = KellyCalculator.calculate_for_zone(zone, win_prob, edge)
        return portfolio_value * kelly_fraction

    @staticmethod
    def validate_edge(edge: Decimal) -> bool:
        """Validate edge is sufficient.

        Args:
            edge: Expected edge

        Returns:
            True if edge >= 5%

        Raises:
            ValueError: If edge < 5%
        """
        if edge < KellyCalculator.MIN_EDGE:
            raise ValueError(
                f"Edge {edge*100:.1f}% below minimum {KellyCalculator.MIN_EDGE*100:.1f}%"
            )
        return True
