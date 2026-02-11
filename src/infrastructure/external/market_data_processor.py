"""Market data processor for orderbook and trade data.

Provides aggregation, normalization, and processing of market data.
"""

import logging
from decimal import Decimal
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MarketDataProcessor:
    """Processes and aggregates market data.

    Provides:
    - Orderbook aggregation
    - Price/liquidity calculations
    - Market snapshot generation
    - Real-time data streaming

    Example:
        >>> processor = MarketDataProcessor()
        >>> orderbook = await processor.process_orderbook(raw_orderbook)
        >>> snapshot = processor.create_market_snapshot(market_id, orderbook)
    """

    def __init__(self) -> None:
        """Initialize market data processor."""
        self._orderbooks: dict[str, dict[str, Any]] = {}
        logger.info("MarketDataProcessor initialized")

    def process_orderbook(
        self, market_id: str, raw_orderbook: dict[str, Any]
    ) -> dict[str, Any]:
        """Process and normalize orderbook.

        Args:
            market_id: Market ID
            raw_orderbook: Raw orderbook from API

        Returns:
            Normalized orderbook dict

        Example:
            >>> orderbook = processor.process_orderbook(
            ...     "market123",
            ...     {"bids": [["0.55", "1000"]], "asks": [["0.56", "2000"]]}
            ... )
        """
        bids = [
            {"price": Decimal(bid[0]), "size": Decimal(bid[1])}
            for bid in raw_orderbook.get("bids", [])
        ]
        asks = [
            {"price": Decimal(ask[0]), "size": Decimal(ask[1])}
            for ask in raw_orderbook.get("asks", [])
        ]

        # Sort bids descending, asks ascending
        bids.sort(key=lambda x: x["price"], reverse=True)
        asks.sort(key=lambda x: x["price"])

        orderbook = {
            "market_id": market_id,
            "bids": bids,
            "asks": asks,
            "timestamp": raw_orderbook.get("timestamp"),
        }

        # Cache orderbook
        self._orderbooks[market_id] = orderbook

        logger.debug(
            "Orderbook processed",
            extra={
                "market_id": market_id,
                "bid_count": len(bids),
                "ask_count": len(asks),
            },
        )

        return orderbook

    def calculate_mid_price(
        self, orderbook: dict[str, Any]
    ) -> Optional[Decimal]:
        """Calculate mid price from orderbook.

        Args:
            orderbook: Processed orderbook

        Returns:
            Mid price or None if no bids/asks
        """
        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])

        if not bids or not asks:
            return None

        best_bid = bids[0]["price"]
        best_ask = asks[0]["price"]

        return (best_bid + best_ask) / Decimal("2")

    def calculate_spread(
        self, orderbook: dict[str, Any]
    ) -> Optional[Decimal]:
        """Calculate bid-ask spread.

        Args:
            orderbook: Processed orderbook

        Returns:
            Spread or None if no bids/asks
        """
        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])

        if not bids or not asks:
            return None

        best_bid = bids[0]["price"]
        best_ask = asks[0]["price"]

        return best_ask - best_bid

    def calculate_liquidity(
        self, orderbook: dict[str, Any], depth: int = 10
    ) -> dict[str, Decimal]:
        """Calculate orderbook liquidity.

        Args:
            orderbook: Processed orderbook
            depth: Number of levels to include

        Returns:
            Dict with bid_liquidity and ask_liquidity
        """
        bids = orderbook.get("bids", [])[:depth]
        asks = orderbook.get("asks", [])[:depth]

        bid_liquidity = sum(bid["size"] for bid in bids)
        ask_liquidity = sum(ask["size"] for ask in asks)

        return {
            "bid_liquidity": bid_liquidity,
            "ask_liquidity": ask_liquidity,
            "total_liquidity": bid_liquidity + ask_liquidity,
        }

    def create_market_snapshot(
        self, market_id: str, orderbook: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Create market snapshot.

        Args:
            market_id: Market ID
            orderbook: Orderbook (uses cached if None)

        Returns:
            Market snapshot dict
        """
        if orderbook is None:
            orderbook = self._orderbooks.get(market_id)
            if orderbook is None:
                raise ValueError(f"No orderbook for market {market_id}")

        mid_price = self.calculate_mid_price(orderbook)
        spread = self.calculate_spread(orderbook)
        liquidity = self.calculate_liquidity(orderbook)

        snapshot = {
            "market_id": market_id,
            "mid_price": mid_price,
            "spread": spread,
            "liquidity": liquidity,
            "timestamp": orderbook.get("timestamp"),
        }

        logger.debug("Market snapshot created", extra={"market_id": market_id})

        return snapshot
