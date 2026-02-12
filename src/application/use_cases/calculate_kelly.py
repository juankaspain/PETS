"""Calculate Kelly use case."""

import logging
from decimal import Decimal

from src.domain.services.kelly_calculator import KellyCalculator
from src.domain.value_objects.zone import Zone

logger = logging.getLogger(__name__)


class CalculateKellyUseCase:
    """Calculate Kelly position sizing use case.

    Workflow:
    1. Validate edge (must be >= 5%)
    2. Calculate Kelly fraction for zone
    3. Calculate position size from portfolio value
    4. Return sizing recommendation

    Example:
        >>> use_case = CalculateKellyUseCase(kelly_calc)
        >>> size = await use_case.execute(
        ...     zone=2,
        ...     win_prob=Decimal("0.60"),
        ...     edge=Decimal("0.15"),
        ...     portfolio_value=Decimal("10000"),
        ... )
        >>> size
        Decimal('1500.00')  # 15% of portfolio
    """

    def __init__(self, kelly_calculator: KellyCalculator) -> None:
        """Initialize use case.

        Args:
            kelly_calculator: Kelly calculator
        """
        self.kelly_calc = kelly_calculator

    async def execute(
        self,
        zone: int,
        win_prob: Decimal,
        edge: Decimal,
        portfolio_value: Decimal,
    ) -> dict:
        """Execute calculate Kelly use case.

        Args:
            zone: Risk zone (1-5)
            win_prob: Win probability (0.0-1.0)
            edge: Expected edge
            portfolio_value: Total portfolio value

        Returns:
            Dict with kelly_fraction and position_size

        Raises:
            ValueError: If edge < 5%
        """
        logger.info(
            "Calculating Kelly",
            extra={
                "zone": zone,
                "win_prob": float(win_prob),
                "edge": float(edge),
                "portfolio_value": float(portfolio_value),
            },
        )

        # 1. Validate edge
        self.kelly_calc.validate_edge(edge)

        # 2. Calculate Kelly fraction
        zone_obj = Zone(zone)
        kelly_fraction = self.kelly_calc.calculate_for_zone(zone_obj, win_prob, edge)

        # 3. Calculate position size
        position_size = self.kelly_calc.calculate_position_size(
            zone_obj, win_prob, edge, portfolio_value
        )

        result = {
            "kelly_fraction": kelly_fraction,
            "position_size": position_size,
            "position_pct": (position_size / portfolio_value * Decimal("100")),
        }

        logger.info(
            "Kelly calculated",
            extra={
                "kelly_fraction": float(kelly_fraction),
                "position_size": float(position_size),
                "position_pct": float(result["position_pct"]),
            },
        )

        return result
