"""Unit tests for Order domain entity.

Tests cover Order creation, validation, state transitions,
and business rules compliance.
"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from src.domain.entities.order import Order
from src.domain.value_objects import (
    OrderId, MarketId, Price, Quantity, Side, OrderStatus, Zone
)
from src.domain.exceptions import (
    InvalidOrderError, ZoneViolationError, OrderRejectedError
)


class TestOrderCreation:
    """Tests for Order entity creation."""

    def test_create_valid_order(self) -> None:
        """Test creating a valid order with all required fields."""
        order = Order(
            order_id=OrderId(str(uuid4())),
            bot_id=8,
            market_id=MarketId("0x" + "a" * 64),
            side=Side.YES,
            size=Quantity(Decimal("100.00")),
            price=Price(Decimal("0.35")),
            zone=Zone.ZONE_2,
            status=OrderStatus.PENDING,
            timestamp=datetime.now(timezone.utc),
            post_only=True
        )
        assert order.bot_id == 8
        assert order.side == Side.YES
        assert order.status == OrderStatus.PENDING
        assert order.post_only is True

    def test_create_order_auto_zone_classification(self) -> None:
        """Test that zone is auto-classified based on price."""
        # Zone 1: 0.05-0.20
        order_z1 = Order(
            order_id=OrderId(str(uuid4())),
            bot_id=8,
            market_id=MarketId("0x" + "b" * 64),
            side=Side.YES,
            size=Quantity(Decimal("50.00")),
            price=Price(Decimal("0.15")),
            timestamp=datetime.now(timezone.utc)
        )
        assert order_z1.zone == Zone.ZONE_1

        # Zone 3: 0.40-0.60
        order_z3 = Order(
            order_id=OrderId(str(uuid4())),
            bot_id=8,
            market_id=MarketId("0x" + "c" * 64),
            side=Side.NO,
            size=Quantity(Decimal("50.00")),
            price=Price(Decimal("0.50")),
            timestamp=datetime.now(timezone.utc)
        )
        assert order_z3.zone == Zone.ZONE_3

    def test_create_order_invalid_price_raises_error(self) -> None:
        """Test that invalid price raises InvalidOrderError."""
        with pytest.raises(InvalidOrderError):
            Order(
                order_id=OrderId(str(uuid4())),
                bot_id=8,
                market_id=MarketId("0x" + "d" * 64),
                side=Side.YES,
                size=Quantity(Decimal("100.00")),
                price=Price(Decimal("1.50")),  # Invalid: > 0.99
                timestamp=datetime.now(timezone.utc)
            )

    def test_create_order_zero_size_raises_error(self) -> None:
        """Test that zero size raises InvalidOrderError."""
        with pytest.raises(InvalidOrderError):
            Order(
                order_id=OrderId(str(uuid4())),
                bot_id=8,
                market_id=MarketId("0x" + "e" * 64),
                side=Side.YES,
                size=Quantity(Decimal("0.00")),  # Invalid: zero
                price=Price(Decimal("0.35")),
                timestamp=datetime.now(timezone.utc)
            )


class TestOrderZoneRestrictions:
    """Tests for zone-based order restrictions."""

    def test_directional_order_zone_4_prohibited(self) -> None:
        """Test that directional orders in Zone 4 are prohibited."""
        with pytest.raises(ZoneViolationError, match="Zone 4-5 directional prohibited"):
            Order(
                order_id=OrderId(str(uuid4())),
                bot_id=8,
                market_id=MarketId("0x" + "f" * 64),
                side=Side.YES,
                size=Quantity(Decimal("100.00")),
                price=Price(Decimal("0.70")),  # Zone 4
                timestamp=datetime.now(timezone.utc),
                is_directional=True
            )

    def test_directional_order_zone_5_prohibited(self) -> None:
        """Test that directional orders in Zone 5 are prohibited."""
        with pytest.raises(ZoneViolationError):
            Order(
                order_id=OrderId(str(uuid4())),
                bot_id=8,
                market_id=MarketId("0x" + "1" * 64),
                side=Side.YES,
                size=Quantity(Decimal("100.00")),
                price=Price(Decimal("0.92")),  # Zone 5
                timestamp=datetime.now(timezone.utc),
                is_directional=True
            )

    def test_market_making_order_zone_4_allowed(self) -> None:
        """Test that market making orders in Zone 4 are allowed."""
        order = Order(
            order_id=OrderId(str(uuid4())),
            bot_id=5,  # MM bot
            market_id=MarketId("0x" + "2" * 64),
            side=Side.YES,
            size=Quantity(Decimal("100.00")),
            price=Price(Decimal("0.70")),
            timestamp=datetime.now(timezone.utc),
            is_directional=False  # MM order
        )
        assert order.zone == Zone.ZONE_4


class TestOrderStatusTransitions:
    """Tests for order status state transitions."""

    @pytest.fixture
    def pending_order(self) -> Order:
        """Create a pending order for testing."""
        return Order(
            order_id=OrderId(str(uuid4())),
            bot_id=8,
            market_id=MarketId("0x" + "3" * 64),
            side=Side.YES,
            size=Quantity(Decimal("100.00")),
            price=Price(Decimal("0.35")),
            status=OrderStatus.PENDING,
            timestamp=datetime.now(timezone.utc)
        )

    def test_transition_pending_to_filled(self, pending_order: Order) -> None:
        """Test valid transition from PENDING to FILLED."""
        pending_order.mark_filled(fill_price=Decimal("0.35"))
        assert pending_order.status == OrderStatus.FILLED

    def test_transition_pending_to_canceled(self, pending_order: Order) -> None:
        """Test valid transition from PENDING to CANCELED."""
        pending_order.cancel(reason="User requested")
        assert pending_order.status == OrderStatus.CANCELED

    def test_transition_pending_to_rejected(self, pending_order: Order) -> None:
        """Test valid transition from PENDING to REJECTED."""
        pending_order.reject(reason="Insufficient balance")
        assert pending_order.status == OrderStatus.REJECTED

    def test_transition_filled_to_canceled_invalid(self, pending_order: Order) -> None:
        """Test that filled orders cannot be canceled."""
        pending_order.mark_filled(fill_price=Decimal("0.35"))
        with pytest.raises(InvalidOrderError, match="Cannot cancel filled order"):
            pending_order.cancel(reason="Too late")


class TestOrderCalculations:
    """Tests for order calculations."""

    def test_calculate_notional_value(self) -> None:
        """Test notional value calculation."""
        order = Order(
            order_id=OrderId(str(uuid4())),
            bot_id=8,
            market_id=MarketId("0x" + "4" * 64),
            side=Side.YES,
            size=Quantity(Decimal("100.00")),
            price=Price(Decimal("0.35")),
            timestamp=datetime.now(timezone.utc)
        )
        # Notional = size * price = 100 * 0.35 = 35
        assert order.notional_value == Decimal("35.00")

    def test_calculate_maker_rebate(self) -> None:
        """Test maker rebate calculation (20% of fee)."""
        order = Order(
            order_id=OrderId(str(uuid4())),
            bot_id=8,
            market_id=MarketId("0x" + "5" * 64),
            side=Side.YES,
            size=Quantity(Decimal("1000.00")),
            price=Price(Decimal("0.50")),
            timestamp=datetime.now(timezone.utc),
            post_only=True
        )
        # Expected rebate: notional * 0.002 * 0.20 = 500 * 0.002 * 0.20 = 0.20
        expected_rebate = Decimal("0.20")
        assert order.calculate_maker_rebate() == expected_rebate


class TestOrderImmutability:
    """Tests for order immutability constraints."""

    def test_order_id_immutable(self) -> None:
        """Test that order_id cannot be changed after creation."""
        order = Order(
            order_id=OrderId(str(uuid4())),
            bot_id=8,
            market_id=MarketId("0x" + "6" * 64),
            side=Side.YES,
            size=Quantity(Decimal("100.00")),
            price=Price(Decimal("0.35")),
            timestamp=datetime.now(timezone.utc)
        )
        with pytest.raises(AttributeError):
            order.order_id = OrderId(str(uuid4()))

    def test_market_id_immutable(self) -> None:
        """Test that market_id cannot be changed after creation."""
        order = Order(
            order_id=OrderId(str(uuid4())),
            bot_id=8,
            market_id=MarketId("0x" + "7" * 64),
            side=Side.YES,
            size=Quantity(Decimal("100.00")),
            price=Price(Decimal("0.35")),
            timestamp=datetime.now(timezone.utc)
        )
        with pytest.raises(AttributeError):
            order.market_id = MarketId("0x" + "8" * 64)


@pytest.mark.parametrize("price,expected_zone", [
    (Decimal("0.05"), Zone.ZONE_1),
    (Decimal("0.15"), Zone.ZONE_1),
    (Decimal("0.20"), Zone.ZONE_1),
    (Decimal("0.25"), Zone.ZONE_2),
    (Decimal("0.35"), Zone.ZONE_2),
    (Decimal("0.40"), Zone.ZONE_2),
    (Decimal("0.45"), Zone.ZONE_3),
    (Decimal("0.55"), Zone.ZONE_3),
    (Decimal("0.60"), Zone.ZONE_3),
    (Decimal("0.65"), Zone.ZONE_4),
    (Decimal("0.75"), Zone.ZONE_4),
    (Decimal("0.80"), Zone.ZONE_4),
    (Decimal("0.85"), Zone.ZONE_5),
    (Decimal("0.95"), Zone.ZONE_5),
    (Decimal("0.98"), Zone.ZONE_5),
])
def test_zone_classification_parametrized(
    price: Decimal, expected_zone: Zone
) -> None:
    """Parametrized test for zone classification based on price."""
    order = Order(
        order_id=OrderId(str(uuid4())),
        bot_id=8,
        market_id=MarketId("0x" + "9" * 64),
        side=Side.YES,
        size=Quantity(Decimal("100.00")),
        price=Price(price),
        timestamp=datetime.now(timezone.utc),
        is_directional=False  # Allow all zones for this test
    )
    assert order.zone == expected_zone
