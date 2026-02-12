"""Unit tests for Position domain entity.

Tests cover Position creation, P&L calculations, close operations,
and risk validation.
"""
import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from src.domain.entities.position import Position
from src.domain.value_objects import (
    PositionId, OrderId, MarketId, Price, Quantity, Side, Zone
)
from src.domain.exceptions import (
    PositionNotFoundError, PositionAlreadyClosedError, InvalidOrderError
)


class TestPositionCreation:
    """Tests for Position entity creation."""

    def test_create_valid_position(self) -> None:
        """Test creating a valid position with all required fields."""
        position = Position(
            position_id=PositionId(str(uuid4())),
            bot_id=8,
            order_id=OrderId(str(uuid4())),
            market_id=MarketId("0x" + "a" * 64),
            side=Side.YES,
            size=Quantity(Decimal("100.00")),
            entry_price=Price(Decimal("0.35")),
            zone=Zone.ZONE_2,
            opened_at=datetime.now(timezone.utc)
        )
        assert position.bot_id == 8
        assert position.side == Side.YES
        assert position.is_open is True
        assert position.closed_at is None

    def test_position_initial_pnl_zero(self) -> None:
        """Test that initial unrealized P&L is zero."""
        position = Position(
            position_id=PositionId(str(uuid4())),
            bot_id=8,
            order_id=OrderId(str(uuid4())),
            market_id=MarketId("0x" + "b" * 64),
            side=Side.YES,
            size=Quantity(Decimal("100.00")),
            entry_price=Price(Decimal("0.35")),
            current_price=Price(Decimal("0.35")),
            opened_at=datetime.now(timezone.utc)
        )
        assert position.unrealized_pnl == Decimal("0.00")


class TestPositionPnLCalculations:
    """Tests for Position P&L calculations."""

    @pytest.fixture
    def long_position(self) -> Position:
        """Create a YES (long) position for testing."""
        return Position(
            position_id=PositionId(str(uuid4())),
            bot_id=8,
            order_id=OrderId(str(uuid4())),
            market_id=MarketId("0x" + "c" * 64),
            side=Side.YES,
            size=Quantity(Decimal("100.00")),
            entry_price=Price(Decimal("0.35")),
            current_price=Price(Decimal("0.35")),
            opened_at=datetime.now(timezone.utc)
        )

    def test_unrealized_pnl_profit_long(self, long_position: Position) -> None:
        """Test unrealized P&L calculation when price goes up (profit)."""
        long_position.update_current_price(Price(Decimal("0.45")))
        # PnL = (0.45 - 0.35) * 100 = 10.00
        assert long_position.unrealized_pnl == Decimal("10.00")

    def test_unrealized_pnl_loss_long(self, long_position: Position) -> None:
        """Test unrealized P&L calculation when price goes down (loss)."""
        long_position.update_current_price(Price(Decimal("0.25")))
        # PnL = (0.25 - 0.35) * 100 = -10.00
        assert long_position.unrealized_pnl == Decimal("-10.00")

    def test_unrealized_pnl_short_position(self) -> None:
        """Test unrealized P&L for NO (short) position."""
        position = Position(
            position_id=PositionId(str(uuid4())),
            bot_id=8,
            order_id=OrderId(str(uuid4())),
            market_id=MarketId("0x" + "d" * 64),
            side=Side.NO,
            size=Quantity(Decimal("100.00")),
            entry_price=Price(Decimal("0.65")),
            current_price=Price(Decimal("0.55")),
            opened_at=datetime.now(timezone.utc)
        )
        # NO position profits when price goes down
        # PnL = (0.65 - 0.55) * 100 = 10.00 (inverted)
        assert position.unrealized_pnl == Decimal("10.00")

    def test_realized_pnl_after_close(self, long_position: Position) -> None:
        """Test realized P&L after closing position."""
        long_position.update_current_price(Price(Decimal("0.50")))
        long_position.close(exit_price=Price(Decimal("0.50")))
        # Realized PnL = (0.50 - 0.35) * 100 = 15.00
        assert long_position.realized_pnl == Decimal("15.00")
        assert long_position.is_open is False


class TestPositionClose:
    """Tests for closing positions."""

    @pytest.fixture
    def open_position(self) -> Position:
        """Create an open position for testing."""
        return Position(
            position_id=PositionId(str(uuid4())),
            bot_id=8,
            order_id=OrderId(str(uuid4())),
            market_id=MarketId("0x" + "e" * 64),
            side=Side.YES,
            size=Quantity(Decimal("100.00")),
            entry_price=Price(Decimal("0.35")),
            opened_at=datetime.now(timezone.utc)
        )

    def test_close_position_sets_closed_at(self, open_position: Position) -> None:
        """Test that closing position sets closed_at timestamp."""
        open_position.close(exit_price=Price(Decimal("0.40")))
        assert open_position.closed_at is not None
        assert open_position.is_open is False

    def test_close_already_closed_raises_error(self, open_position: Position) -> None:
        """Test that closing already closed position raises error."""
        open_position.close(exit_price=Price(Decimal("0.40")))
        with pytest.raises(PositionAlreadyClosedError):
            open_position.close(exit_price=Price(Decimal("0.45")))

    def test_close_records_hold_duration(self, open_position: Position) -> None:
        """Test that hold duration is recorded on close."""
        open_position.close(exit_price=Price(Decimal("0.40")))
        assert open_position.hold_duration is not None
        assert open_position.hold_duration >= timedelta(seconds=0)


class TestPositionDrawdown:
    """Tests for position drawdown calculations."""

    def test_drawdown_calculation(self) -> None:
        """Test maximum drawdown calculation."""
        position = Position(
            position_id=PositionId(str(uuid4())),
            bot_id=8,
            order_id=OrderId(str(uuid4())),
            market_id=MarketId("0x" + "f" * 64),
            side=Side.YES,
            size=Quantity(Decimal("100.00")),
            entry_price=Price(Decimal("0.50")),
            current_price=Price(Decimal("0.50")),
            opened_at=datetime.now(timezone.utc)
        )
        # Simulate price dropping to 0.40 (20% drawdown)
        position.update_current_price(Price(Decimal("0.40")))
        # Drawdown = (0.50 - 0.40) / 0.50 = 0.20 = 20%
        assert position.current_drawdown == Decimal("0.20")

    def test_max_drawdown_tracking(self) -> None:
        """Test that max drawdown is tracked over time."""
        position = Position(
            position_id=PositionId(str(uuid4())),
            bot_id=8,
            order_id=OrderId(str(uuid4())),
            market_id=MarketId("0x" + "1" * 64),
            side=Side.YES,
            size=Quantity(Decimal("100.00")),
            entry_price=Price(Decimal("0.50")),
            current_price=Price(Decimal("0.50")),
            opened_at=datetime.now(timezone.utc)
        )
        # Price drops to 0.35 (30% drawdown)
        position.update_current_price(Price(Decimal("0.35")))
        # Price recovers to 0.45
        position.update_current_price(Price(Decimal("0.45")))
        # Max drawdown should still be 30%
        assert position.max_drawdown == Decimal("0.30")


class TestPositionImmutability:
    """Tests for position immutability."""

    def test_position_id_immutable(self) -> None:
        """Test that position_id cannot be changed."""
        position = Position(
            position_id=PositionId(str(uuid4())),
            bot_id=8,
            order_id=OrderId(str(uuid4())),
            market_id=MarketId("0x" + "2" * 64),
            side=Side.YES,
            size=Quantity(Decimal("100.00")),
            entry_price=Price(Decimal("0.35")),
            opened_at=datetime.now(timezone.utc)
        )
        with pytest.raises(AttributeError):
            position.position_id = PositionId(str(uuid4()))

    def test_entry_price_immutable(self) -> None:
        """Test that entry_price cannot be changed."""
        position = Position(
            position_id=PositionId(str(uuid4())),
            bot_id=8,
            order_id=OrderId(str(uuid4())),
            market_id=MarketId("0x" + "3" * 64),
            side=Side.YES,
            size=Quantity(Decimal("100.00")),
            entry_price=Price(Decimal("0.35")),
            opened_at=datetime.now(timezone.utc)
        )
        with pytest.raises(AttributeError):
            position.entry_price = Price(Decimal("0.40"))


@pytest.mark.parametrize("entry,current,expected_pnl", [
    (Decimal("0.30"), Decimal("0.40"), Decimal("10.00")),  # +10%
    (Decimal("0.50"), Decimal("0.60"), Decimal("10.00")),  # +10%
    (Decimal("0.40"), Decimal("0.30"), Decimal("-10.00")),  # -10%
    (Decimal("0.25"), Decimal("0.25"), Decimal("0.00")),   # flat
])
def test_pnl_parametrized(
    entry: Decimal, current: Decimal, expected_pnl: Decimal
) -> None:
    """Parametrized test for P&L calculations."""
    position = Position(
        position_id=PositionId(str(uuid4())),
        bot_id=8,
        order_id=OrderId(str(uuid4())),
        market_id=MarketId("0x" + "4" * 64),
        side=Side.YES,
        size=Quantity(Decimal("100.00")),
        entry_price=Price(entry),
        current_price=Price(current),
        opened_at=datetime.now(timezone.utc)
    )
    assert position.unrealized_pnl == expected_pnl
