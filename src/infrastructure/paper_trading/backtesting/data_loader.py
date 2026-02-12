"""Historical data loader for backtesting."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List

logger = logging.getLogger(__name__)


class HistoricalDataLoader:
    """Loads historical market data for backtesting.

    Fetches data from Polymarket API or TimescaleDB.
    Caches data for performance.
    """

    def __init__(self):
        """Initialize data loader."""
        self.cache: dict[str, List[tuple[datetime, Decimal]]] = {}

        logger.info("Historical data loader initialized")

    def load_price_data(
        self,
        market_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[tuple[datetime, Decimal]]:
        """Load historical price data.

        Args:
            market_id: Market ID
            start_date: Start date
            end_date: End date

        Returns:
            List of (timestamp, price) tuples
        """
        cache_key = f"{market_id}_{start_date}_{end_date}"

        # Check cache
        if cache_key in self.cache:
            logger.info(
                "Price data loaded from cache",
                extra={"market_id": market_id, "data_points": len(self.cache[cache_key])},
            )
            return self.cache[cache_key]

        # TODO: Fetch from Polymarket API or TimescaleDB
        # For now, generate synthetic data
        logger.warning(
            "Generating synthetic price data (TODO: implement real data fetch)"
        )

        data = self._generate_synthetic_data(start_date, end_date)
        self.cache[cache_key] = data

        logger.info(
            "Price data loaded",
            extra={"market_id": market_id, "data_points": len(data)},
        )

        return data

    def _generate_synthetic_data(
        self,
        start_date: datetime,
        end_date: datetime,
        initial_price: Decimal = Decimal("0.50"),
    ) -> List[tuple[datetime, Decimal]]:
        """Generate synthetic price data for testing.

        Args:
            start_date: Start date
            end_date: End date
            initial_price: Initial price

        Returns:
            List of (timestamp, price) tuples
        """
        import random
        from datetime import timedelta

        data = []
        current_date = start_date
        current_price = initial_price

        while current_date <= end_date:
            # Random walk with mean reversion
            change = Decimal(str(random.gauss(0, 0.02)))  # 2% std dev
            mean_reversion = (Decimal("0.50") - current_price) * Decimal("0.1")
            current_price += change + mean_reversion

            # Clamp to [0.01, 0.99]
            current_price = max(Decimal("0.01"), min(Decimal("0.99"), current_price))

            data.append((current_date, current_price))
            current_date += timedelta(hours=1)  # Hourly data

        return data

    def clear_cache(self) -> None:
        """Clear data cache."""
        self.cache.clear()
        logger.info("Data cache cleared")
