"""Market simulator for paper trading."""

import logging
import random
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict

logger = logging.getLogger(__name__)


@dataclass
class MarketSnapshot:
    """Market snapshot at a point in time."""

    market_id: str
    timestamp: datetime
    yes_price: Decimal
    no_price: Decimal
    liquidity: Decimal
    volume_24h: Decimal
    spread: Decimal


class MarketSimulator:
    """Market simulator for generating synthetic market data.

    Useful for testing when historical data is not available.
    """

    def __init__(self, seed: int | None = None):
        """Initialize market simulator.

        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)

    def generate_market_snapshot(
        self,
        market_id: str,
        base_price: Decimal = Decimal("0.50"),
        volatility: Decimal = Decimal("0.05"),
        liquidity: Decimal = Decimal("50000"),
    ) -> MarketSnapshot:
        """Generate synthetic market snapshot.

        Args:
            market_id: Market ID
            base_price: Base YES price (default 0.50)
            volatility: Price volatility (default 0.05)
            liquidity: Market liquidity (default $50K)

        Returns:
            Market snapshot
        """
        # Random walk from base price
        price_change = Decimal(str(random.gauss(0, float(volatility))))
        yes_price = max(
            Decimal("0.01"),
            min(Decimal("0.99"), base_price + price_change),
        )
        no_price = Decimal("1.0") - yes_price

        # Spread (bid-ask)
        spread = Decimal(str(random.uniform(0.01, 0.05)))

        # Volume
        volume_24h = liquidity * Decimal(str(random.uniform(0.1, 0.5)))

        return MarketSnapshot(
            market_id=market_id,
            timestamp=datetime.utcnow(),
            yes_price=yes_price,
            no_price=no_price,
            liquidity=liquidity,
            volume_24h=volume_24h,
            spread=spread,
        )

    def generate_price_series(
        self,
        market_id: str,
        start_price: Decimal,
        num_points: int,
        volatility: Decimal = Decimal("0.05"),
    ) -> list[Decimal]:
        """Generate price series using random walk.

        Args:
            market_id: Market ID
            start_price: Starting price
            num_points: Number of price points
            volatility: Volatility parameter

        Returns:
            List of prices
        """
        prices = [start_price]
        current_price = start_price

        for _ in range(num_points - 1):
            # Random walk
            change = Decimal(str(random.gauss(0, float(volatility))))
            current_price = max(
                Decimal("0.01"),
                min(Decimal("0.99"), current_price + change),
            )
            prices.append(current_price)

        return prices

    def simulate_bot8_opportunity(
        self,
        market_id: str,
        entry_type: str = "cheap_yes",  # "cheap_yes" or "expensive_no"
    ) -> list[MarketSnapshot]:
        """Simulate Bot 8 trading opportunity.

        Args:
            market_id: Market ID
            entry_type: Type of opportunity

        Returns:
            List of market snapshots showing opportunity and mean reversion
        """
        snapshots = []

        if entry_type == "cheap_yes":
            # Cheap YES (<0.20) with spread >15%
            entry_price = Decimal("0.15")
            spread = Decimal("0.20")  # 20% spread

            # Generate mean reversion to ~0.40
            prices = self.generate_price_series(
                market_id=market_id,
                start_price=entry_price,
                num_points=48,  # 48 hours
                volatility=Decimal("0.02"),
            )

            # Add upward drift for mean reversion
            for i, price in enumerate(prices):
                drift = Decimal(str(i)) * Decimal("0.005")
                prices[i] = min(Decimal("0.99"), price + drift)

        else:  # expensive_no
            # Expensive NO (>0.80) = Cheap YES (<0.20)
            entry_price = Decimal("0.85")
            spread = Decimal("0.25")

            # Generate mean reversion to ~0.60
            prices = self.generate_price_series(
                market_id=market_id,
                start_price=entry_price,
                num_points=48,
                volatility=Decimal("0.02"),
            )

            # Add downward drift
            for i, price in enumerate(prices):
                drift = Decimal(str(i)) * Decimal("0.005")
                prices[i] = max(Decimal("0.01"), price - drift)

        # Create snapshots
        base_time = datetime.utcnow()
        for i, price in enumerate(prices):
            from datetime import timedelta
            snapshot = MarketSnapshot(
                market_id=market_id,
                timestamp=base_time + timedelta(hours=i),
                yes_price=price,
                no_price=Decimal("1.0") - price,
                liquidity=Decimal("50000"),
                volume_24h=Decimal("10000"),
                spread=spread,
            )
            snapshots.append(snapshot)

        logger.info(
            "Simulated Bot 8 opportunity",
            extra={
                "market_id": market_id,
                "entry_type": entry_type,
                "entry_price": float(entry_price),
                "snapshots": len(snapshots),
            },
        )

        return snapshots
