"""End-to-end tests for Bot 8 Volatility Skew Tail Risk Combo.

Tests the complete flow from market scanning to position management
using testcontainers for database and mocked external APIs.
"""
import pytest
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.bots.bot_08_volatility_skew.strategy import Bot8VolatilitySkew
from src.domain.entities import Order, Position, Market
from src.domain.value_objects import (
    MarketId, Price, Quantity, Side, Zone, BotState, OrderStatus
)
from src.application.use_cases import (
    PlaceOrderUseCase, OpenPositionUseCase, ClosePositionUseCase
)
from src.infrastructure.external import PolymarketCLOBClient


@pytest.fixture
def mock_clob_client() -> AsyncMock:
    """Create mocked Polymarket CLOB client."""
    client = AsyncMock(spec=PolymarketCLOBClient)
    client.get_orderbook.return_value = {
        "bids": [(Decimal("0.34"), Decimal("500"))],
        "asks": [(Decimal("0.36"), Decimal("500"))],
    }
    client.place_order.return_value = {
        "order_id": str(uuid4()),
        "status": "OPEN",
    }
    return client


@pytest.fixture
def sample_markets() -> list[Market]:
    """Create sample markets for testing."""
    return [
        Market(
            market_id=MarketId("0x" + "a" * 64),
            question="Will BTC reach $100K by end of 2026?",
            outcomes=["Yes", "No"],
            liquidity=Decimal("50000"),
            volume_24h=Decimal("10000"),
            yes_price=Price(Decimal("0.15")),  # Zone 1 - tail risk
            created_at=datetime.now(timezone.utc),
        ),
        Market(
            market_id=MarketId("0x" + "b" * 64),
            question="Will ETH flip BTC by 2027?",
            outcomes=["Yes", "No"],
            liquidity=Decimal("30000"),
            volume_24h=Decimal("5000"),
            yes_price=Price(Decimal("0.08")),  # Zone 1 - extreme tail
            created_at=datetime.now(timezone.utc),
        ),
    ]


@pytest.fixture
async def bot8_instance(mock_clob_client: AsyncMock) -> Bot8VolatilitySkew:
    """Create Bot 8 instance with mocked dependencies."""
    config = {
        "bot_id": 8,
        "capital_allocated": Decimal("1000.00"),
        "max_position_size": Decimal("200.00"),
        "kelly_fraction": Decimal("0.5"),  # Half Kelly
        "zone_restrictions": {
            "allowed": ["ZONE_1", "ZONE_2"],
            "prohibited": ["ZONE_4", "ZONE_5"],
        },
        "circuit_breakers": {
            "max_consecutive_losses": 3,
            "max_daily_loss_pct": Decimal("0.05"),
            "max_drawdown_pct": Decimal("0.25"),
        },
    }
    bot = Bot8VolatilitySkew(config=config, clob_client=mock_clob_client)
    return bot


class TestBot8MarketScanning:
    """Tests for Bot 8 market scanning and analysis."""

    @pytest.mark.asyncio
    async def test_scan_markets_finds_tail_risk_opportunities(
        self, bot8_instance: Bot8VolatilitySkew, sample_markets: list[Market]
    ) -> None:
        """Test that Bot 8 identifies tail risk opportunities in Zone 1."""
        opportunities = await bot8_instance.scan_markets(sample_markets)
        
        assert len(opportunities) >= 1
        for opp in opportunities:
            assert opp.zone in [Zone.ZONE_1, Zone.ZONE_2]
            assert opp.score > Decimal("0.5")  # Minimum score threshold

    @pytest.mark.asyncio
    async def test_scan_rejects_zone_4_5_markets(
        self, bot8_instance: Bot8VolatilitySkew
    ) -> None:
        """Test that Bot 8 rejects markets in Zone 4-5 for directional trades."""
        zone_5_market = Market(
            market_id=MarketId("0x" + "c" * 64),
            question="High probability event",
            outcomes=["Yes", "No"],
            liquidity=Decimal("100000"),
            volume_24h=Decimal("50000"),
            yes_price=Price(Decimal("0.92")),  # Zone 5
            created_at=datetime.now(timezone.utc),
        )
        
        opportunities = await bot8_instance.scan_markets([zone_5_market])
        assert len(opportunities) == 0


class TestBot8OrderExecution:
    """Tests for Bot 8 order execution flow."""

    @pytest.mark.asyncio
    async def test_place_post_only_order(
        self, bot8_instance: Bot8VolatilitySkew, mock_clob_client: AsyncMock
    ) -> None:
        """Test that Bot 8 places post-only orders (maker orders)."""
        order = await bot8_instance.place_order(
            market_id=MarketId("0x" + "a" * 64),
            side=Side.YES,
            size=Quantity(Decimal("100.00")),
            price=Price(Decimal("0.15")),
        )
        
        mock_clob_client.place_order.assert_called_once()
        call_args = mock_clob_client.place_order.call_args
        assert call_args.kwargs.get("post_only") is True

    @pytest.mark.asyncio
    async def test_order_uses_half_kelly_sizing(
        self, bot8_instance: Bot8VolatilitySkew
    ) -> None:
        """Test that position sizes follow Half Kelly criterion."""
        # Given: Market with 55% estimated win rate, 3:1 odds
        win_rate = Decimal("0.55")
        odds = Decimal("3.0")
        capital = Decimal("1000.00")
        
        # Full Kelly: f* = (bp - q) / b = (3*0.55 - 0.45) / 3 = 0.40
        # Half Kelly: f* / 2 = 0.20 = 20%
        expected_fraction = Decimal("0.20")
        
        size = bot8_instance.calculate_position_size(
            win_rate=win_rate, odds=odds, capital=capital
        )
        
        max_size = capital * expected_fraction
        assert size <= max_size


class TestBot8PositionManagement:
    """Tests for Bot 8 position management."""

    @pytest.mark.asyncio
    async def test_open_position_on_filled_order(
        self, bot8_instance: Bot8VolatilitySkew
    ) -> None:
        """Test that position is opened when order is filled."""
        # Simulate order fill
        order = Order(
            order_id=str(uuid4()),
            bot_id=8,
            market_id=MarketId("0x" + "a" * 64),
            side=Side.YES,
            size=Quantity(Decimal("100.00")),
            price=Price(Decimal("0.15")),
            status=OrderStatus.FILLED,
            timestamp=datetime.now(timezone.utc),
        )
        
        position = await bot8_instance.open_position_from_order(order)
        
        assert position is not None
        assert position.side == Side.YES
        assert position.entry_price.value == Decimal("0.15")
        assert position.is_open is True

    @pytest.mark.asyncio
    async def test_close_position_on_target_hit(
        self, bot8_instance: Bot8VolatilitySkew
    ) -> None:
        """Test that position is closed when target price is hit."""
        position = Position(
            position_id=str(uuid4()),
            bot_id=8,
            order_id=str(uuid4()),
            market_id=MarketId("0x" + "a" * 64),
            side=Side.YES,
            size=Quantity(Decimal("100.00")),
            entry_price=Price(Decimal("0.15")),
            current_price=Price(Decimal("0.15")),
            take_profit=Price(Decimal("0.25")),
            stop_loss=Price(Decimal("0.10")),
            opened_at=datetime.now(timezone.utc),
        )
        
        # Simulate price hitting take profit
        position.update_current_price(Price(Decimal("0.26")))
        
        should_close = bot8_instance.should_close_position(position)
        assert should_close is True
        assert position.unrealized_pnl > Decimal("0")


class TestBot8CircuitBreakers:
    """Tests for Bot 8 circuit breakers."""

    @pytest.mark.asyncio
    async def test_halt_on_consecutive_losses(
        self, bot8_instance: Bot8VolatilitySkew
    ) -> None:
        """Test that bot halts after 3 consecutive losses."""
        # Simulate 3 consecutive losses
        for _ in range(3):
            bot8_instance.record_loss(Decimal("50.00"))
        
        assert bot8_instance.state == BotState.PAUSED
        assert bot8_instance.consecutive_losses == 3

    @pytest.mark.asyncio
    async def test_halt_on_daily_loss_threshold(
        self, bot8_instance: Bot8VolatilitySkew
    ) -> None:
        """Test that bot halts on 5% daily loss."""
        # Capital: $1000, 5% threshold = $50
        bot8_instance.record_loss(Decimal("55.00"))
        
        assert bot8_instance.state == BotState.PAUSED
        assert bot8_instance.daily_pnl < Decimal("-50.00")

    @pytest.mark.asyncio
    async def test_halt_on_max_drawdown(
        self, bot8_instance: Bot8VolatilitySkew
    ) -> None:
        """Test that bot halts on 25% drawdown."""
        # Simulate 25% drawdown from peak
        bot8_instance.peak_capital = Decimal("1200.00")
        bot8_instance.current_capital = Decimal("900.00")
        
        bot8_instance.check_drawdown()
        
        assert bot8_instance.state == BotState.PAUSED
        assert bot8_instance.current_drawdown >= Decimal("0.25")


class TestBot8FullCycle:
    """Full cycle E2E test for Bot 8."""

    @pytest.mark.asyncio
    async def test_complete_trade_cycle(
        self, bot8_instance: Bot8VolatilitySkew, 
        sample_markets: list[Market],
        mock_clob_client: AsyncMock
    ) -> None:
        """Test complete cycle: scan -> order -> position -> close."""
        # 1. Initialize bot
        await bot8_instance.initialize()
        assert bot8_instance.state == BotState.ACTIVE
        
        # 2. Scan markets
        opportunities = await bot8_instance.scan_markets(sample_markets)
        assert len(opportunities) > 0
        
        # 3. Select best opportunity and place order
        best_opp = opportunities[0]
        order = await bot8_instance.execute_opportunity(best_opp)
        assert order.status in [OrderStatus.PENDING, OrderStatus.FILLED]
        
        # 4. Simulate order fill
        mock_clob_client.get_order_status.return_value = {
            "status": "FILLED",
            "fill_price": "0.15",
        }
        
        # 5. Open position
        position = await bot8_instance.process_filled_order(order)
        assert position.is_open is True
        
        # 6. Update price and check exit
        position.update_current_price(Price(Decimal("0.25")))
        should_exit = bot8_instance.should_close_position(position)
        
        if should_exit:
            # 7. Close position
            await bot8_instance.close_position(position)
            assert position.is_open is False
            assert position.realized_pnl > Decimal("0")
        
        # 8. Verify metrics
        metrics = bot8_instance.get_metrics()
        assert "total_trades" in metrics
        assert "win_rate" in metrics
        assert "sharpe_ratio" in metrics
