"""Unit tests for Bot 05: Market Making Strategy."""

import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from src.bots.bot_05_market_making import (
    MarketMakingStrategy,
    MarketQuote,
    InventoryState,
)
from src.bots.base_bot import BotState
from src.domain.entities.order import OrderSide, OrderStatus
from src.domain.value_objects.price import Price
from src.domain.value_objects.size import Size
from src.domain.value_objects.zone import Zone


@pytest.fixture
def base_config():
    """Base config for market making bot."""
    return {
        "capital_allocated": 5000,
        "max_positions": 10,
        "cycle_interval_seconds": 5,
        "base_spread_bps": 50,
        "min_spread_bps": 20,
        "max_spread_bps": 200,
        "max_inventory_imbalance": 0.30,
        "target_markets": 20,
        "liquidity_threshold_usdc": 5000,
        "kelly_fraction": 0.5,
    }


@pytest.fixture
def market_quote_z2():
    """Market quote in Zone 2."""
    return MarketQuote(
        market_id="0x123abc",
        mid_price=Decimal("0.30"),
        bid_price=Decimal("0.295"),
        ask_price=Decimal("0.305"),
        spread_bps=Decimal("50"),
        liquidity_usdc=Decimal("10000"),
        volatility=Decimal("0.05"),
        zone=2,
        last_update=datetime.utcnow(),
    )


@pytest.fixture
def market_quote_z4():
    """Market quote in Zone 4."""
    return MarketQuote(
        market_id="0x456def",
        mid_price=Decimal("0.70"),
        bid_price=Decimal("0.695"),
        ask_price=Decimal("0.705"),
        spread_bps=Decimal("50"),
        liquidity_usdc=Decimal("8000"),
        volatility=Decimal("0.08"),
        zone=4,
        last_update=datetime.utcnow(),
    )


@pytest.fixture
def balanced_inventory():
    """Balanced inventory state."""
    return InventoryState(
        long_size=Decimal("1000"),
        short_size=Decimal("1000"),
        net_size=Decimal("0"),
        imbalance_ratio=Decimal("0"),
        total_value_usdc=Decimal("600"),
    )


@pytest.fixture
def imbalanced_inventory():
    """Imbalanced inventory (long heavy)."""
    return InventoryState(
        long_size=Decimal("1500"),
        short_size=Decimal("500"),
        net_size=Decimal("1000"),
        imbalance_ratio=Decimal("0.50"),  # 50% long heavy
        total_value_usdc=Decimal("600"),
    )


class TestMarketMakingInitialization:
    """Test bot initialization and config validation."""

    def test_valid_config(self, base_config):
        """Test bot initializes with valid config."""
        bot = MarketMakingStrategy(
            bot_id=5, strategy_type="market_making", config=base_config
        )
        assert bot.bot_id == 5
        assert bot.strategy_type == "market_making"
        assert bot.get_state() == BotState.IDLE
        assert bot.base_spread_bps == Decimal("50")
        assert bot.kelly_fraction == Decimal("0.5")

    def test_missing_required_config(self):
        """Test initialization fails with missing config."""
        invalid_config = {"capital_allocated": 5000}  # Missing base_spread_bps
        with pytest.raises(ValueError, match="Missing required config key"):
            MarketMakingStrategy(
                bot_id=5, strategy_type="market_making", config=invalid_config
            )

    def test_invalid_kelly_fraction(self, base_config):
        """Test initialization fails with Full Kelly (>0.5)."""
        base_config["kelly_fraction"] = 1.0  # Full Kelly PROHIBIDO
        with pytest.raises(ValueError, match="Full Kelly PROHIBITED"):
            MarketMakingStrategy(
                bot_id=5, strategy_type="market_making", config=base_config
            )

    def test_zero_capital(self, base_config):
        """Test initialization fails with zero capital."""
        base_config["capital_allocated"] = 0
        with pytest.raises(ValueError, match="capital_allocated must be > 0"):
            MarketMakingStrategy(
                bot_id=5, strategy_type="market_making", config=base_config
            )


class TestSpreadOptimization:
    """Test optimal spread calculation."""

    def test_base_spread_high_liquidity(self, base_config, market_quote_z2):
        """Test base spread with high liquidity (no adjustment)."""
        bot = MarketMakingStrategy(
            bot_id=5, strategy_type="market_making", config=base_config
        )
        spread = bot._calculate_optimal_spread(market_quote_z2)
        assert spread == Decimal("50")  # Base spread, no multiplier

    def test_spread_low_liquidity(self, base_config, market_quote_z2):
        """Test spread widens with low liquidity."""
        bot = MarketMakingStrategy(
            bot_id=5, strategy_type="market_making", config=base_config
        )
        market_quote_z2.liquidity_usdc = Decimal("3000")  # Low liquidity
        spread = bot._calculate_optimal_spread(market_quote_z2)
        assert spread > Decimal("50")  # Should widen

    def test_spread_high_volatility(self, base_config, market_quote_z2):
        """Test spread widens with high volatility."""
        bot = MarketMakingStrategy(
            bot_id=5, strategy_type="market_making", config=base_config
        )
        market_quote_z2.volatility = Decimal("0.15")  # High volatility
        spread = bot._calculate_optimal_spread(market_quote_z2)
        assert spread > Decimal("50")  # Should widen

    def test_spread_zone_4_adjustment(self, base_config, market_quote_z4):
        """Test spread widens in Zone 4."""
        bot = MarketMakingStrategy(
            bot_id=5, strategy_type="market_making", config=base_config
        )
        spread = bot._calculate_optimal_spread(market_quote_z4)
        assert spread > Decimal("50")  # Zone 4 multiplier

    def test_spread_clamping(self, base_config, market_quote_z2):
        """Test spread is clamped to min/max."""
        bot = MarketMakingStrategy(
            bot_id=5, strategy_type="market_making", config=base_config
        )
        # Force very wide spread
        market_quote_z2.liquidity_usdc = Decimal("1000")
        market_quote_z2.volatility = Decimal("0.50")
        spread = bot._calculate_optimal_spread(market_quote_z2)
        assert spread <= bot.max_spread_bps  # Clamped to max


class TestInventoryManagement:
    """Test inventory state and skew calculations."""

    def test_balanced_inventory_no_skew(self, base_config, balanced_inventory):
        """Test balanced inventory produces no skew."""
        bot = MarketMakingStrategy(
            bot_id=5, strategy_type="market_making", config=base_config
        )
        skew = bot._calculate_skew(balanced_inventory)
        assert skew == Decimal("0")

    def test_imbalanced_inventory_produces_skew(self, base_config, imbalanced_inventory):
        """Test imbalanced inventory produces skew."""
        bot = MarketMakingStrategy(
            bot_id=5, strategy_type="market_making", config=base_config
        )
        skew = bot._calculate_skew(imbalanced_inventory)
        assert skew != Decimal("0")  # Should have skew

    def test_inventory_is_balanced_check(self, balanced_inventory):
        """Test inventory balance check."""
        assert balanced_inventory.is_balanced(Decimal("0.30"))

    def test_inventory_is_imbalanced_check(self, imbalanced_inventory):
        """Test inventory imbalance check."""
        assert not imbalanced_inventory.is_balanced(Decimal("0.30"))

    def test_inventory_needs_skew(self, imbalanced_inventory):
        """Test skew threshold detection."""
        assert imbalanced_inventory.needs_skew(Decimal("0.15"))

    def test_skew_direction_long_heavy(self, base_config):
        """Test skew direction for long-heavy inventory."""
        bot = MarketMakingStrategy(
            bot_id=5, strategy_type="market_making", config=base_config
        )
        long_heavy = InventoryState(
            long_size=Decimal("2000"),
            short_size=Decimal("500"),
            net_size=Decimal("1500"),
            imbalance_ratio=Decimal("0.60"),  # 60% long
            total_value_usdc=Decimal("750"),
        )
        skew = bot._calculate_skew(long_heavy)
        # Long heavy should produce positive skew (encourage selling)
        assert skew > Decimal("0")


class TestQuoteGeneration:
    """Test bid/ask quote generation."""

    @pytest.mark.asyncio
    async def test_generate_quotes_z2(self, base_config, market_quote_z2):
        """Test quote generation for Zone 2 market."""
        bot = MarketMakingStrategy(
            bot_id=5, strategy_type="market_making", config=base_config
        )
        bot._active_markets[market_quote_z2.market_id] = market_quote_z2
        bot._inventory[market_quote_z2.market_id] = InventoryState(
            long_size=Decimal("0"),
            short_size=Decimal("0"),
            net_size=Decimal("0"),
            imbalance_ratio=Decimal("0"),
            total_value_usdc=Decimal("0"),
        )

        bid_order, ask_order = await bot._generate_quotes(market_quote_z2)

        # Verify orders created
        assert bid_order.side == OrderSide.BUY
        assert ask_order.side == OrderSide.SELL
        assert bid_order.post_only is True  # OBLIGATORIO
        assert ask_order.post_only is True  # OBLIGATORIO
        assert bid_order.price.value < market_quote_z2.mid_price
        assert ask_order.price.value > market_quote_z2.mid_price

    @pytest.mark.asyncio
    async def test_quotes_respect_spread(self, base_config, market_quote_z2):
        """Test generated quotes respect calculated spread."""
        bot = MarketMakingStrategy(
            bot_id=5, strategy_type="market_making", config=base_config
        )
        bot._active_markets[market_quote_z2.market_id] = market_quote_z2
        bot._inventory[market_quote_z2.market_id] = InventoryState(
            long_size=Decimal("0"),
            short_size=Decimal("0"),
            net_size=Decimal("0"),
            imbalance_ratio=Decimal("0"),
            total_value_usdc=Decimal("0"),
        )

        bid_order, ask_order = await bot._generate_quotes(market_quote_z2)

        # Verify spread width
        spread = ask_order.price.value - bid_order.price.value
        assert spread > Decimal("0")  # Positive spread

    @pytest.mark.asyncio
    async def test_quotes_clamped_to_valid_range(self, base_config, market_quote_z2):
        """Test quotes are clamped to [0.01, 0.99]."""
        bot = MarketMakingStrategy(
            bot_id=5, strategy_type="market_making", config=base_config
        )
        # Market at extreme price
        market_quote_z2.mid_price = Decimal("0.02")
        bot._active_markets[market_quote_z2.market_id] = market_quote_z2
        bot._inventory[market_quote_z2.market_id] = InventoryState(
            long_size=Decimal("0"),
            short_size=Decimal("0"),
            net_size=Decimal("0"),
            imbalance_ratio=Decimal("0"),
            total_value_usdc=Decimal("0"),
        )

        bid_order, ask_order = await bot._generate_quotes(market_quote_z2)

        # Verify clamping
        assert bid_order.price.value >= Decimal("0.01")
        assert ask_order.price.value <= Decimal("0.99")


class TestPositionSizing:
    """Test Half Kelly position sizing."""

    def test_position_size_calculation(self, base_config, market_quote_z2):
        """Test position size uses Half Kelly."""
        bot = MarketMakingStrategy(
            bot_id=5, strategy_type="market_making", config=base_config
        )
        size = bot._calculate_position_size(market_quote_z2)
        assert isinstance(size, Size)
        assert size.value > Decimal("0")

    def test_position_size_respects_capital(self, base_config, market_quote_z2):
        """Test position size respects allocated capital."""
        bot = MarketMakingStrategy(
            bot_id=5, strategy_type="market_making", config=base_config
        )
        size = bot._calculate_position_size(market_quote_z2)
        # Size * price should be <= capital_per_market
        capital_per_market = Decimal(str(base_config["capital_allocated"])) / Decimal(
            str(base_config["target_markets"])
        )
        position_value = size.value * market_quote_z2.mid_price
        # Half Kelly means position_value ~= capital_per_market * 0.5
        assert position_value <= capital_per_market


class TestMarketSelection:
    """Test market selection logic."""

    @pytest.mark.asyncio
    async def test_select_markets_filters_low_liquidity(self, base_config):
        """Test markets below liquidity threshold are filtered."""
        bot = MarketMakingStrategy(
            bot_id=5, strategy_type="market_making", config=base_config
        )
        # Add markets with varying liquidity
        bot._active_markets["high_liq"] = MarketQuote(
            market_id="high_liq",
            mid_price=Decimal("0.50"),
            bid_price=Decimal("0.495"),
            ask_price=Decimal("0.505"),
            spread_bps=Decimal("50"),
            liquidity_usdc=Decimal("10000"),  # Above threshold
            volatility=Decimal("0.05"),
            zone=2,
            last_update=datetime.utcnow(),
        )
        bot._active_markets["low_liq"] = MarketQuote(
            market_id="low_liq",
            mid_price=Decimal("0.50"),
            bid_price=Decimal("0.495"),
            ask_price=Decimal("0.505"),
            spread_bps=Decimal("50"),
            liquidity_usdc=Decimal("1000"),  # Below threshold
            volatility=Decimal("0.05"),
            zone=2,
            last_update=datetime.utcnow(),
        )

        selected = await bot._select_markets()

        # Only high liquidity market selected
        assert len(selected) == 1
        assert selected[0].market_id == "high_liq"

    @pytest.mark.asyncio
    async def test_select_markets_prefers_z2_z3(self, base_config):
        """Test market selection prefers Zone 2-3."""
        bot = MarketMakingStrategy(
            bot_id=5, strategy_type="market_making", config=base_config
        )
        # Add markets in different zones
        for zone in [1, 2, 3, 4]:
            bot._active_markets[f"zone_{zone}"] = MarketQuote(
                market_id=f"zone_{zone}",
                mid_price=Decimal("0.50"),
                bid_price=Decimal("0.495"),
                ask_price=Decimal("0.505"),
                spread_bps=Decimal("50"),
                liquidity_usdc=Decimal("10000"),
                volatility=Decimal("0.05"),
                zone=zone,
                last_update=datetime.utcnow(),
            )

        selected = await bot._select_markets()

        # Only Z2-Z3 markets selected
        selected_zones = [m.zone for m in selected]
        assert all(zone in (2, 3) for zone in selected_zones)


class TestMetrics:
    """Test bot metrics tracking."""

    def test_initial_metrics(self, base_config):
        """Test initial metrics state."""
        bot = MarketMakingStrategy(
            bot_id=5, strategy_type="market_making", config=base_config
        )
        metrics = bot.get_metrics()
        assert metrics.bot_id == 5
        assert metrics.strategy_type == "market_making"
        assert metrics.state == BotState.IDLE
        assert metrics.cycles_completed == 0
        assert metrics.errors_count == 0

    def test_metrics_after_start(self, base_config):
        """Test metrics update correctly."""
        bot = MarketMakingStrategy(
            bot_id=5, strategy_type="market_making", config=base_config
        )
        # Simulate some activity
        bot._orders_placed = 10
        bot._positions_opened = 5
        bot._current_pnl = 123.45

        metrics = bot.get_metrics()
        assert metrics.orders_placed == 10
        assert metrics.positions_opened == 5
        assert metrics.current_pnl == 123.45
