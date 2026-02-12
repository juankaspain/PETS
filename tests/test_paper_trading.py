"""Tests for paper trading infrastructure."""

import pytest
from datetime import datetime
from decimal import Decimal

from src.infrastructure.paper_trading.paper_wallet import PaperWallet
from src.infrastructure.paper_trading.simulated_execution import SimulatedExecution


class TestPaperWallet:
    """Test paper wallet."""

    def test_initialization(self):
        """Test wallet initialization."""
        wallet = PaperWallet(initial_balance=Decimal("10000"))
        assert wallet.get_balance() == Decimal("10000")
        assert len(wallet.get_open_positions()) == 0

    def test_place_order_insufficient_balance(self):
        """Test place order with insufficient balance."""
        wallet = PaperWallet(initial_balance=Decimal("100"))
        
        with pytest.raises(ValueError, match="Insufficient balance"):
            wallet.place_order(
                market_id="test_market",
                side="BUY",
                size=Decimal("1000"),
                price=Decimal("0.50"),
            )

    def test_fill_and_close_position(self):
        """Test fill order and close position."""
        wallet = PaperWallet(initial_balance=Decimal("10000"))
        
        # Place and fill order
        order_id = wallet.place_order(
            market_id="test_market",
            side="BUY",
            size=Decimal("100"),
            price=Decimal("0.50"),
        )
        
        position_id = wallet.fill_order(
            order_id=order_id,
            market_id="test_market",
            side="BUY",
            size=Decimal("100"),
            fill_price=Decimal("0.50"),
        )
        
        assert len(wallet.get_open_positions()) == 1
        
        # Close position with profit
        realized_pnl = wallet.close_position(
            position_id=position_id,
            exit_price=Decimal("0.60"),
        )
        
        # Profit = (0.60 - 0.50) * 100 = 10
        assert realized_pnl == Decimal("10")
        assert len(wallet.get_open_positions()) == 0
        assert len(wallet.get_closed_positions()) == 1

    def test_statistics(self):
        """Test wallet statistics."""
        wallet = PaperWallet(initial_balance=Decimal("10000"))
        
        # Winning trade
        order_id = wallet.place_order("m1", "BUY", Decimal("100"), Decimal("0.50"))
        pos_id = wallet.fill_order(order_id, "m1", "BUY", Decimal("100"), Decimal("0.50"))
        wallet.close_position(pos_id, Decimal("0.60"))
        
        # Losing trade
        order_id = wallet.place_order("m2", "BUY", Decimal("100"), Decimal("0.50"))
        pos_id = wallet.fill_order(order_id, "m2", "BUY", Decimal("100"), Decimal("0.50"))
        wallet.close_position(pos_id, Decimal("0.40"))
        
        stats = wallet.get_statistics({})
        
        assert stats["total_trades"] == 2
        assert stats["winning_trades"] == 1
        assert stats["losing_trades"] == 1
        assert stats["win_rate"] == 0.5


class TestSimulatedExecution:
    """Test simulated execution."""

    def test_submit_order_taker_prohibited(self):
        """Test taker orders are prohibited."""
        wallet = PaperWallet(Decimal("10000"))
        execution = SimulatedExecution(wallet)
        
        with pytest.raises(ValueError, match="Taker orders prohibited"):
            execution.submit_order(
                market_id="test",
                side="BUY",
                size=Decimal("100"),
                price=Decimal("0.50"),
                post_only=False,
            )

    def test_order_fill_on_market_update(self):
        """Test order fills when market price crosses limit."""
        wallet = PaperWallet(Decimal("10000"))
        execution = SimulatedExecution(wallet)
        
        # Submit buy order at 0.50
        order_id = execution.submit_order(
            market_id="test",
            side="BUY",
            size=Decimal("100"),
            price=Decimal("0.50"),
            post_only=True,
        )
        
        # Market at 0.60 - no fill
        filled = execution.process_market_update("test", Decimal("0.60"))
        assert len(filled) == 0
        
        # Market drops to 0.50 - order fills
        filled = execution.process_market_update("test", Decimal("0.50"))
        assert len(filled) == 1
        assert filled[0] == order_id
        
        # Position created
        assert len(wallet.get_open_positions()) == 1

    def test_cancel_order(self):
        """Test order cancellation."""
        wallet = PaperWallet(Decimal("10000"))
        execution = SimulatedExecution(wallet)
        
        order_id = execution.submit_order(
            market_id="test",
            side="BUY",
            size=Decimal("100"),
            price=Decimal("0.50"),
        )
        
        # Balance reserved
        assert wallet.get_balance() < Decimal("10000")
        
        # Cancel order
        execution.cancel_order(order_id)
        
        # Balance returned
        assert wallet.get_balance() == Decimal("10000")
