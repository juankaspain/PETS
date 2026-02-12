"""Market simulator for paper trading."""

import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict

logger = logging.getLogger(__name__)


@dataclass
class MarketSnapshot:
    """Market data snapshot."""

    market_id: str
    timestamp: datetime
    yes_price: Decimal
    no_price: Decimal
    liquidity: Decimal
    volume_24h: Decimal
    spread: Decimal


class MarketSimulator:
    """Simulates market data for paper trading.

    Generates price feeds and market updates.
    Can replay historical data or generate synthetic data.
    """

    def __init__(self):
        """Initialize market simulator."""
        self.markets: Dict[str, MarketSnapshot] = {}
        self.price_history: Dict[str, list[tuple[datetime, Decimal]]] = {}

        logger.info("Market simulator initialized")

    def add_market(
        self,
        market_id: str,
        initial_yes_price: Decimal,
        initial_no_price: Decimal,
        liquidity: Decimal = Decimal("100000"),
        volume_24h: Decimal = Decimal("50000"),
    ) -> None:
        """Add market to simulator.

        Args:
            market_id: Market ID
            initial_yes_price: Initial YES price
            initial_no_price: Initial NO price
            liquidity: Market liquidity
            volume_24h: 24h volume
        """
        spread = abs(initial_yes_price - Decimal("0.5")) * 2

        snapshot = MarketSnapshot(
            market_id=market_id,
            timestamp=datetime.utcnow(),
            yes_price=initial_yes_price,
            no_price=initial_no_price,
            liquidity=liquidity,
            volume_24h=volume_24h,
            spread=spread,
        )

        self.markets[market_id] = snapshot
        self.price_history[market_id] = [(snapshot.timestamp, initial_yes_price)]

        logger.info(
            "Market added",
            extra={
                "market_id": market_id,
                "yes_price": float(initial_yes_price),
                "no_price": float(initial_no_price),
                "spread": float(spread),
            },
        )

    def update_price(
        self,
        market_id: str,
        new_yes_price: Decimal,
    ) -> MarketSnapshot:
        """Update market price.

        Args:
            market_id: Market ID
            new_yes_price: New YES price

        Returns:
            Updated snapshot

        Raises:
            ValueError: If market not found
        """
        if market_id not in self.markets:
            raise ValueError(f"Market {market_id} not found")

        snapshot = self.markets[market_id]
        snapshot.yes_price = new_yes_price
        snapshot.no_price = Decimal("1.0") - new_yes_price
        snapshot.spread = abs(new_yes_price - Decimal("0.5")) * 2
        snapshot.timestamp = datetime.utcnow()

        # Update history
        self.price_history[market_id].append((snapshot.timestamp, new_yes_price))

        logger.debug(
            "Price updated",
            extra={
                "market_id": market_id,
                "yes_price": float(new_yes_price),
                "spread": float(snapshot.spread),
            },
        )

        return snapshot

    def get_current_price(self, market_id: str) -> Decimal:
        """Get current price for market.

        Args:
            market_id: Market ID

        Returns:
            Current YES price

        Raises:
            ValueError: If market not found
        """
        if market_id not in self.markets:
            raise ValueError(f"Market {market_id} not found")

        return self.markets[market_id].yes_price

    def get_snapshot(self, market_id: str) -> MarketSnapshot:
        """Get market snapshot.

        Args:
            market_id: Market ID

        Returns:
            Market snapshot

        Raises:
            ValueError: If market not found
        """
        if market_id not in self.markets:
            raise ValueError(f"Market {market_id} not found")

        return self.markets[market_id]

    def get_price_history(
        self,
        market_id: str,
    ) -> list[tuple[datetime, Decimal]]:
        """Get price history for market.

        Args:
            market_id: Market ID

        Returns:
            List of (timestamp, price) tuples
        """
        return self.price_history.get(market_id, [])
