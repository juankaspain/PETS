"""Unit tests for paper trading engine.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import pytest
from decimal import Decimal

from src.application.paper_trading.paper_trading_engine import (
    PaperTradingConfig,
    PaperTradingEngine,
    VirtualBalance,
    VirtualPosition,
)
from src.domain.entities.order import OrderSide, OrderType
from src.domain.entities.position import PositionSide


@pytest.fixture
def config() -> PaperTradingConfig:
    """Create test config."""
    return PaperTradingConfig(
        initial_balance=5000.0,
        simulate_slippage=True,
        simulate_fees=True,
        simulate_latency_ms=10,  # Fast for tests
    )


@pytest.fixture
def engine(config: PaperTradingConfig) -> PaperTradingEngine:
    """Create test engine."""
    return PaperTradingEngine(bot_id=8, config=config)


class TestVirtualBalance:
    """Test VirtualBalance."""

    def test_total_balance(self) -> None:
        """Test total balance calculation."""
        balance = VirtualBalance(available=1000.0, reserved=500.0)
        assert balance.total == 1500.0

    def test_initial_state(self) -> None:
        """Test initial state."""
        balance = VirtualBalance(available=5000.0)
        assert balance.available == 5000.0
        assert balance.reserved == 0.0
        assert balance.total == 5000.0


class TestVirtualPosition:
    """Test VirtualPosition."""

    def test_unrealized_pnl_yes_profit(self) -> None:
        """Test unrealized P&L for YES position (profit)."""
        from datetime import datetime
        
        position = VirtualPosition(
            position_id="pos_1",
            market_id="market_1",
            side=PositionSide.YES,
            size=100.0,
            entry_price=0.60,
            current_price=0.70,
            opened_at=datetime.now(),
            bot_id=8,
        )
        
        assert position.unrealized_pnl == pytest.approx(10.0)  # (0.70 - 0.60) * 100

    def test_unrealized_pnl_yes_loss(self) -> None:
        """Test unrealized P&L for YES position (loss)."""
        from datetime import datetime
        
        position = VirtualPosition(
            position_id="pos_1",
            market_id="market_1",
            side=PositionSide.YES,
            size=100.0,
            entry_price=0.70,
            current_price=0.60,
            opened_at=datetime.now(),
            bot_id=8,
        )
        
        assert position.unrealized_pnl == pytest.approx(-10.0)

    def test_unrealized_pnl_no_profit(self) -> None:
        """Test unrealized P&L for NO position (profit)."""
        from datetime import datetime
        
        position = VirtualPosition(
            position_id="pos_1",
            market_id="market_1",
            side=PositionSide.NO,
            size=100.0,
            entry_price=0.70,
            current_price=0.60,
            opened_at=datetime.now(),
            bot_id=8,
        )
        
        assert position.unrealized_pnl == pytest.approx(10.0)  # (0.70 - 0.60) * 100

    def test_position_value(self) -> None:
        """Test position value calculation."""
        from datetime import datetime
        
        position = VirtualPosition(
            position_id="pos_1",
            market_id="market_1",
            side=PositionSide.YES,
            size=100.0,
            entry_price=0.60,
            current_price=0.70,
            opened_at=datetime.now(),
            bot_id=8,
        )
        
        assert position.value == pytest.approx(70.0)  # 0.70 * 100


class TestPaperTradingEngine:
    """Test PaperTradingEngine."""

    def test_initialization(self, engine: PaperTradingEngine) -> None:
        """Test engine initialization."""
        assert engine.balance.available == 5000.0
        assert engine.balance.reserved == 0.0
        assert len(engine.positions) == 0
        assert engine.total_pnl == 0.0
        assert engine.portfolio_value == 5000.0

    @pytest.mark.asyncio
    async def test_place_order_success(self, engine: PaperTradingEngine) -> None:
        """Test successful order placement."""
        order = await engine.place_order(
            market_id="market_1",
            side=OrderSide.YES,
            size=100.0,
            price=0.65,
            order_type=OrderType.POST_ONLY,
        )
        
        assert order.market_id == "market_1"
        assert order.side == OrderSide.YES
        assert order.size == Decimal("100.0")
        assert order.price == Decimal("0.65")
        
        # Balance should be reserved
        assert engine.balance.reserved == pytest.approx(65.0)  # 100 * 0.65
        assert engine.balance.available == pytest.approx(4935.0)  # 5000 - 65

    @pytest.mark.asyncio
    async def test_place_order_insufficient_balance(self, engine: PaperTradingEngine) -> None:
        """Test order rejection due to insufficient balance."""
        with pytest.raises(ValueError, match="Insufficient balance"):
            await engine.place_order(
                market_id="market_1",
                side=OrderSide.YES,
                size=10000.0,  # Too large
                price=0.65,
                order_type=OrderType.POST_ONLY,
            )

    @pytest.mark.asyncio
    async def test_cancel_order(self, engine: PaperTradingEngine) -> None:
        """Test order cancellation."""
        order = await engine.place_order(
            market_id="market_1",
            side=OrderSide.YES,
            size=100.0,
            price=0.65,
            order_type=OrderType.POST_ONLY,
        )
        
        # Cancel immediately (before fill)
        await engine.cancel_order(order.order_id)
        
        # Balance should be released
        assert engine.balance.available == pytest.approx(5000.0)
        assert engine.balance.reserved == pytest.approx(0.0)

    @pytest.mark.asyncio
    async def test_close_position(self, engine: PaperTradingEngine) -> None:
        """Test position closure."""
        # Place and wait for fill
        order = await engine.place_order(
            market_id="market_1",
            side=OrderSide.YES,
            size=100.0,
            price=0.65,
            order_type=OrderType.LIMIT,  # Use LIMIT for immediate fill in test
        )
        
        # Wait for execution
        import asyncio
        await asyncio.sleep(0.1)
        
        # Should have position
        positions = engine.positions
        if positions:
            position = positions[0]
            
            # Update current price for P&L
            position.current_price = 0.75  # Simulated price increase
            
            # Close position
            pnl = await engine.close_position(position.position_id)
            
            # Should have realized profit
            assert pnl > 0  # Profit after fees/slippage
            assert len(engine.positions) == 0

    def test_performance_summary(self, engine: PaperTradingEngine) -> None:
        """Test performance summary generation."""
        summary = engine.get_performance_summary()
        
        assert "initial_balance" in summary
        assert "current_balance" in summary
        assert "portfolio_value" in summary
        assert "realized_pnl" in summary
        assert "unrealized_pnl" in summary
        assert "total_pnl" in summary
        assert "total_fees" in summary
        assert "open_positions" in summary
        assert "roi" in summary
        
        assert summary["initial_balance"] == 5000.0
        assert summary["roi"] == 0.0  # No trades yet

    def test_reset(self, engine: PaperTradingEngine) -> None:
        """Test engine reset."""
        # Modify state
        engine._realized_pnl = 100.0
        engine._total_fees_paid = 10.0
        engine._balance.available = 4500.0
        
        # Reset
        engine.reset()
        
        # Should be back to initial state
        assert engine.balance.available == 5000.0
        assert engine.balance.reserved == 0.0
        assert engine._realized_pnl == 0.0
        assert engine._total_fees_paid == 0.0
        assert len(engine.positions) == 0
