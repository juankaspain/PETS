"""Bot 05: Market Making Strategy.

Makes markets in Z2-Z3 with optimized spreads, capturing maker rebates.
Uses Half Kelly sizing with inventory management and skew adjustment.

Strategy:
    - Dual-sided quoting: buy and sell orders simultaneously
    - Spread optimization: based on liquidity, volatility, zone
    - Inventory management: skew quotes when inventory imbalanced
    - Post-only ONLY: 20% maker rebates
    - Focus Z2-Z3: 0.20-0.60 range
    - Z4-Z5: arbitrage mode only (no directional)

Example config:
    capital_allocated: 5000  # $5K
    max_positions: 10
    cycle_interval_seconds: 5
    base_spread_bps: 50  # 0.50%
    min_spread_bps: 20  # 0.20%
    max_spread_bps: 200  # 2.00%
    max_inventory_imbalance: 0.30  # 30%
    target_markets: 20
    liquidity_threshold_usdc: 5000
    kelly_fraction: 0.5  # Half Kelly
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from src.bots.base_bot import BaseBotStrategy
from src.domain.entities.order import Order, OrderSide, OrderStatus
from src.domain.value_objects.price import Price
from src.domain.value_objects.size import Size
from src.domain.value_objects.zone import Zone

logger = logging.getLogger(__name__)


@dataclass
class MarketQuote:
    """Market quote with bid/ask."""

    market_id: str
    mid_price: Decimal
    bid_price: Decimal
    ask_price: Decimal
    spread_bps: Decimal
    liquidity_usdc: Decimal
    volatility: Decimal
    zone: int
    last_update: datetime


@dataclass
class InventoryState:
    """Current inventory state."""

    long_size: Decimal
    short_size: Decimal
    net_size: Decimal
    imbalance_ratio: Decimal  # -1.0 to 1.0
    total_value_usdc: Decimal

    def is_balanced(self, max_imbalance: Decimal) -> bool:
        """Check if inventory is balanced."""
        return abs(self.imbalance_ratio) <= max_imbalance

    def needs_skew(self, threshold: Decimal = Decimal("0.15")) -> bool:
        """Check if quotes should be skewed."""
        return abs(self.imbalance_ratio) > threshold


class MarketMakingStrategy(BaseBotStrategy):
    """Bot 05: Market Making Strategy.

    Provides liquidity with dual-sided quotes, earning maker rebates.
    Manages inventory risk with skew adjustments.

    Example:
        >>> bot = MarketMakingStrategy(
        ...     bot_id=5,
        ...     strategy_type="market_making",
        ...     config={
        ...         "capital_allocated": 5000,
        ...         "max_positions": 10,
        ...         "cycle_interval_seconds": 5,
        ...         "base_spread_bps": 50,
        ...         "kelly_fraction": 0.5,
        ...     },
        ... )
        >>> await bot.start()
    """

    def __init__(self, bot_id: int, strategy_type: str, config: Dict) -> None:
        """Initialize market making strategy.

        Args:
            bot_id: Bot identifier
            strategy_type: "market_making"
            config: Strategy configuration

        Raises:
            ValueError: If config validation fails
        """
        super().__init__(bot_id, strategy_type, config)

        # Market making specific config
        self.base_spread_bps: Decimal = Decimal(str(config["base_spread_bps"]))
        self.min_spread_bps: Decimal = Decimal(str(config.get("min_spread_bps", 20)))
        self.max_spread_bps: Decimal = Decimal(str(config.get("max_spread_bps", 200)))
        self.max_inventory_imbalance: Decimal = Decimal(
            str(config.get("max_inventory_imbalance", 0.30))
        )
        self.target_markets: int = config.get("target_markets", 20)
        self.liquidity_threshold: Decimal = Decimal(
            str(config.get("liquidity_threshold_usdc", 5000))
        )
        self.kelly_fraction: Decimal = Decimal(str(config.get("kelly_fraction", 0.5)))

        # Validate Half Kelly (Full Kelly PROHIBIDO)
        if self.kelly_fraction > Decimal("0.5"):
            raise ValueError(
                f"kelly_fraction {self.kelly_fraction} > 0.5 - Full Kelly PROHIBITED"
            )

        # Runtime state
        self._active_markets: Dict[str, MarketQuote] = {}
        self._active_orders: Dict[str, Order] = {}
        self._inventory: Dict[str, InventoryState] = {}
        self._rebates_earned: Decimal = Decimal("0")
        self._spread_captured_total: Decimal = Decimal("0")

    def _validate_config(self) -> None:
        """Validate market making config.

        Raises:
            ValueError: If config invalid
        """
        super()._validate_config()

        required_keys = ["base_spread_bps"]
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required config key: {key}")

        if Decimal(str(self.config["base_spread_bps"])) <= 0:
            raise ValueError("base_spread_bps must be > 0")

    async def initialize(self) -> None:
        """Initialize market making bot.

        Setup:
        - WebSocket connections to CLOB
        - Market data subscriptions
        - Load active positions

        Raises:
            ConnectionError: If WebSocket fails
        """
        logger.info(
            "market_making_initializing",
            extra={
                "bot_id": self.bot_id,
                "base_spread_bps": float(self.base_spread_bps),
                "target_markets": self.target_markets,
                "kelly_fraction": float(self.kelly_fraction),
            },
        )

        # TODO: Initialize WebSocket client
        # TODO: Subscribe to market data feeds
        # TODO: Load existing positions from DB
        # TODO: Sync inventory state

        # Placeholder: Mark as initialized
        await asyncio.sleep(0.1)

        logger.info(
            "market_making_initialized",
            extra={"bot_id": self.bot_id, "active_markets": len(self._active_markets)},
        )

    async def execute_cycle(self) -> None:
        """Execute one market making cycle.

        Steps:
        1. Update market data (WebSocket)
        2. Calculate optimal spreads
        3. Check inventory state
        4. Generate quotes (skewed if needed)
        5. Cancel stale orders
        6. Place new orders (post-only)

        Raises:
            Exception: If cycle fails
        """
        logger.debug(
            "market_making_cycle_start",
            extra={
                "bot_id": self.bot_id,
                "active_markets": len(self._active_markets),
                "active_orders": len(self._active_orders),
            },
        )

        # Step 1: Update market data
        await self._update_market_data()

        # Step 2: Select target markets
        target_markets = await self._select_markets()

        # Step 3: Calculate inventory state
        await self._update_inventory_state()

        # Step 4: Generate quotes for each market
        quotes_to_place: List[Tuple[Order, Order]] = []
        for market in target_markets:
            try:
                bid_order, ask_order = await self._generate_quotes(market)
                quotes_to_place.append((bid_order, ask_order))
            except Exception as e:
                logger.warning(
                    "quote_generation_failed",
                    extra={"bot_id": self.bot_id, "market_id": market.market_id, "error": str(e)},
                )

        # Step 5: Cancel stale orders
        await self._cancel_stale_orders()

        # Step 6: Place new quotes
        await self._place_quotes(quotes_to_place)

        logger.debug(
            "market_making_cycle_complete",
            extra={
                "bot_id": self.bot_id,
                "quotes_placed": len(quotes_to_place) * 2,
                "rebates_earned": float(self._rebates_earned),
            },
        )

    async def stop_gracefully(self) -> None:
        """Stop market making gracefully.

        Cleanup:
        - Cancel all open orders
        - Close WebSocket connections
        - Save final metrics

        Raises:
            Exception: If cleanup fails
        """
        logger.info(
            "market_making_stopping",
            extra={
                "bot_id": self.bot_id,
                "active_orders": len(self._active_orders),
                "rebates_earned": float(self._rebates_earned),
            },
        )

        # Cancel all orders
        await self._cancel_all_orders()

        # TODO: Close WebSocket connections
        # TODO: Save final metrics to DB

        logger.info(
            "market_making_stopped",
            extra={
                "bot_id": self.bot_id,
                "total_spread_captured": float(self._spread_captured_total),
                "total_rebates": float(self._rebates_earned),
            },
        )

    async def _update_market_data(self) -> None:
        """Update market data from WebSocket.

        Updates self._active_markets with latest quotes.
        """
        # TODO: Fetch from WebSocket feed
        # Placeholder: simulate market data
        pass

    async def _select_markets(self) -> List[MarketQuote]:
        """Select markets for quoting.

        Criteria:
        - Liquidity > threshold
        - Zone 2-3 preferred
        - Volatility moderate
        - Active markets only

        Returns:
            List of MarketQuote to quote
        """
        eligible_markets = [
            market
            for market in self._active_markets.values()
            if market.liquidity_usdc >= self.liquidity_threshold
            and market.zone in (2, 3)  # Z2-Z3 focus
        ]

        # Sort by liquidity (higher = better)
        eligible_markets.sort(key=lambda m: m.liquidity_usdc, reverse=True)

        return eligible_markets[: self.target_markets]

    async def _update_inventory_state(self) -> None:
        """Update inventory state for all markets.

        Calculates net position and imbalance ratio.
        """
        # TODO: Query DB for open positions
        # Placeholder: assume balanced inventory
        for market_id in self._active_markets:
            if market_id not in self._inventory:
                self._inventory[market_id] = InventoryState(
                    long_size=Decimal("0"),
                    short_size=Decimal("0"),
                    net_size=Decimal("0"),
                    imbalance_ratio=Decimal("0"),
                    total_value_usdc=Decimal("0"),
                )

    async def _generate_quotes(
        self, market: MarketQuote
    ) -> Tuple[Order, Order]:
        """Generate bid/ask quotes for market.

        Applies:
        - Spread optimization (liquidity, volatility, zone)
        - Inventory skew adjustment
        - Half Kelly position sizing
        - Post-only enforcement

        Args:
            market: MarketQuote to generate quotes for

        Returns:
            Tuple of (bid_order, ask_order)

        Raises:
            ValueError: If zone restrictions violated
        """
        # Calculate optimal spread
        spread_bps = self._calculate_optimal_spread(market)

        # Get inventory state
        inventory = self._inventory.get(
            market.market_id,
            InventoryState(
                long_size=Decimal("0"),
                short_size=Decimal("0"),
                net_size=Decimal("0"),
                imbalance_ratio=Decimal("0"),
                total_value_usdc=Decimal("0"),
            ),
        )

        # Apply skew if imbalanced
        skew_bps = self._calculate_skew(inventory)

        # Calculate bid/ask prices
        half_spread = spread_bps / Decimal("2") / Decimal("10000")  # bps to decimal
        skew_adjustment = skew_bps / Decimal("10000")

        bid_price_value = market.mid_price - half_spread + skew_adjustment
        ask_price_value = market.mid_price + half_spread + skew_adjustment

        # Clamp to valid range [0.01, 0.99]
        bid_price_value = max(Decimal("0.01"), min(bid_price_value, Decimal("0.98")))
        ask_price_value = max(Decimal("0.02"), min(ask_price_value, Decimal("0.99")))

        # Create Price objects (auto-classifies zone)
        bid_price = Price(bid_price_value)
        ask_price = Price(ask_price_value)

        # Calculate position size (Half Kelly)
        size = self._calculate_position_size(market)

        # Create orders (post-only OBLIGATORIO)
        bid_order = Order(
            order_id=uuid4(),
            bot_id=self.bot_id,
            market_id=market.market_id,
            side=OrderSide.BUY,
            size=size,
            price=bid_price,
            zone=Zone(bid_price.zone),
            status=OrderStatus.PENDING,
            post_only=True,  # OBLIGATORIO
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        ask_order = Order(
            order_id=uuid4(),
            bot_id=self.bot_id,
            market_id=market.market_id,
            side=OrderSide.SELL,
            size=size,
            price=ask_price,
            zone=Zone(ask_price.zone),
            status=OrderStatus.PENDING,
            post_only=True,  # OBLIGATORIO
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        logger.debug(
            "quotes_generated",
            extra={
                "bot_id": self.bot_id,
                "market_id": market.market_id,
                "bid_price": float(bid_price.value),
                "ask_price": float(ask_price.value),
                "spread_bps": float(spread_bps),
                "skew_bps": float(skew_bps),
                "size": float(size.value),
            },
        )

        return bid_order, ask_order

    def _calculate_optimal_spread(self, market: MarketQuote) -> Decimal:
        """Calculate optimal spread based on market conditions.

        Factors:
        - Base spread (config)
        - Liquidity (lower = wider spread)
        - Volatility (higher = wider spread)
        - Zone (Z4-Z5 = wider spread)

        Args:
            market: MarketQuote

        Returns:
            Optimal spread in basis points
        """
        spread = self.base_spread_bps

        # Liquidity adjustment: lower liquidity = wider spread
        if market.liquidity_usdc < Decimal("10000"):
            spread *= Decimal("1.5")
        elif market.liquidity_usdc < Decimal("5000"):
            spread *= Decimal("2.0")

        # Volatility adjustment
        if market.volatility > Decimal("0.10"):
            spread *= Decimal("1.3")

        # Zone adjustment: Z4-Z5 wider
        if market.zone in (4, 5):
            spread *= Decimal("1.5")

        # Clamp to min/max
        spread = max(self.min_spread_bps, min(spread, self.max_spread_bps))

        return spread

    def _calculate_skew(self, inventory: InventoryState) -> Decimal:
        """Calculate quote skew based on inventory imbalance.

        Skew direction:
        - Long heavy: skew DOWN (encourage selling)
        - Short heavy: skew UP (encourage buying)

        Args:
            inventory: Current InventoryState

        Returns:
            Skew adjustment in basis points
        """
        if not inventory.needs_skew():
            return Decimal("0")

        # Skew proportional to imbalance
        skew_bps = inventory.imbalance_ratio * Decimal("50")  # max 50 bps

        return skew_bps

    def _calculate_position_size(self, market: MarketQuote) -> Size:
        """Calculate position size using Half Kelly.

        Args:
            market: MarketQuote

        Returns:
            Size for order
        """
        # Simplified: allocate equal capital per market
        capital_per_market = (
            Decimal(str(self.config["capital_allocated"])) / Decimal(str(self.target_markets))
        )

        # Half Kelly fraction
        size_usdc = capital_per_market * self.kelly_fraction

        # Convert to contract size (assuming 1 USDC = 1 contract)
        size_value = size_usdc / market.mid_price

        return Size(size_value)

    async def _cancel_stale_orders(self) -> None:
        """Cancel orders that are stale or off-market.

        Stale criteria:
        - Price > 2% away from mid
        - Order > 60 seconds old
        """
        # TODO: Query active orders from exchange
        # TODO: Cancel stale orders
        pass

    async def _place_quotes(self, quotes: List[Tuple[Order, Order]]) -> None:
        """Place bid/ask quotes on exchange.

        Args:
            quotes: List of (bid_order, ask_order) tuples
        """
        for bid_order, ask_order in quotes:
            try:
                # TODO: Submit orders to exchange via CLOB client
                # Placeholder: track in memory
                self._active_orders[str(bid_order.order_id)] = bid_order
                self._active_orders[str(ask_order.order_id)] = ask_order
                self._orders_placed += 2

                logger.debug(
                    "quotes_placed",
                    extra={
                        "bot_id": self.bot_id,
                        "market_id": bid_order.market_id,
                        "bid_id": str(bid_order.order_id),
                        "ask_id": str(ask_order.order_id),
                    },
                )

            except Exception as e:
                logger.error(
                    "quote_placement_failed",
                    extra={
                        "bot_id": self.bot_id,
                        "market_id": bid_order.market_id,
                        "error": str(e),
                    },
                    exc_info=True,
                )

    async def _cancel_all_orders(self) -> None:
        """Cancel all active orders."""
        logger.info(
            "cancelling_all_orders",
            extra={"bot_id": self.bot_id, "count": len(self._active_orders)},
        )

        # TODO: Batch cancel via CLOB client
        self._active_orders.clear()
