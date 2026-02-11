"""Enumerations for domain value objects."""

from enum import Enum


class Side(str, Enum):
    """Order side (YES or NO)."""

    YES = "YES"
    NO = "NO"

    def opposite(self) -> "Side":
        """Get opposite side.

        Returns:
            Opposite side (YES -> NO, NO -> YES)

        Example:
            >>> Side.YES.opposite()
            Side.NO
        """
        return Side.NO if self == Side.YES else Side.YES


class OrderStatus(str, Enum):
    """Order status lifecycle."""

    PENDING = "PENDING"  # Order created, not yet submitted
    SUBMITTED = "SUBMITTED"  # Order submitted to exchange
    OPEN = "OPEN"  # Order open on exchange
    PARTIALLY_FILLED = "PARTIALLY_FILLED"  # Order partially executed
    FILLED = "FILLED"  # Order fully executed
    CANCELED = "CANCELED"  # Order canceled by user
    REJECTED = "REJECTED"  # Order rejected by exchange
    EXPIRED = "EXPIRED"  # Order expired (time limit)

    @property
    def is_terminal(self) -> bool:
        """Check if status is terminal (no further transitions).

        Returns:
            True if status is FILLED, CANCELED, REJECTED, or EXPIRED
        """
        return self in (
            OrderStatus.FILLED,
            OrderStatus.CANCELED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED,
        )

    @property
    def is_active(self) -> bool:
        """Check if order is active on exchange.

        Returns:
            True if status is OPEN or PARTIALLY_FILLED
        """
        return self in (OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED)


class BotState(str, Enum):
    """Bot state machine.

    State transitions:
    IDLE -> STARTING -> ACTIVE <-> PAUSED -> STOPPING -> STOPPED
                                 -> ERROR
                                 -> EMERGENCY_HALT
    """

    IDLE = "IDLE"  # Bot initialized but not started
    STARTING = "STARTING"  # Bot startup in progress
    ACTIVE = "ACTIVE"  # Bot actively trading
    PAUSED = "PAUSED"  # Bot paused (can resume)
    STOPPING = "STOPPING"  # Bot graceful shutdown in progress
    STOPPED = "STOPPED"  # Bot stopped cleanly
    ERROR = "ERROR"  # Bot in error state
    EMERGENCY_HALT = "EMERGENCY_HALT"  # Bot emergency halted

    @property
    def can_start(self) -> bool:
        """Check if bot can be started from this state."""
        return self in (BotState.IDLE, BotState.STOPPED)

    @property
    def can_pause(self) -> bool:
        """Check if bot can be paused from this state."""
        return self == BotState.ACTIVE

    @property
    def can_resume(self) -> bool:
        """Check if bot can be resumed from this state."""
        return self == BotState.PAUSED

    @property
    def can_stop(self) -> bool:
        """Check if bot can be stopped from this state."""
        return self in (BotState.ACTIVE, BotState.PAUSED, BotState.ERROR)

    @property
    def is_running(self) -> bool:
        """Check if bot is in a running state."""
        return self in (BotState.ACTIVE, BotState.PAUSED)


class Zone(int, Enum):
    """Price zones for risk classification.

    Zone ranges:
    - ZONE_1: 0.05-0.20 (tail risk, contrarian - directional OK)
    - ZONE_2: 0.20-0.40 (value betting - directional OK)
    - ZONE_3: 0.40-0.60 (arb/MM only - edge required)
    - ZONE_4: 0.60-0.80 (arb/MM only - directional PROHIBITED)
    - ZONE_5: 0.80-0.98 (arb/MM only - directional PROHIBITED)
    """

    ZONE_1 = 1
    ZONE_2 = 2
    ZONE_3 = 3
    ZONE_4 = 4
    ZONE_5 = 5

    @property
    def allows_directional(self) -> bool:
        """Check if zone allows directional trading.

        Returns:
            True for Zone 1-2, False for Zone 3-5
        """
        return self in (Zone.ZONE_1, Zone.ZONE_2)

    @property
    def requires_edge_calculation(self) -> bool:
        """Check if zone requires edge calculation.

        Returns:
            True for Zone 3+
        """
        return self.value >= 3

    @property
    def min_price(self) -> float:
        """Get minimum price for this zone."""
        ranges = {
            Zone.ZONE_1: 0.05,
            Zone.ZONE_2: 0.20,
            Zone.ZONE_3: 0.40,
            Zone.ZONE_4: 0.60,
            Zone.ZONE_5: 0.80,
        }
        return ranges[self]

    @property
    def max_price(self) -> float:
        """Get maximum price for this zone."""
        ranges = {
            Zone.ZONE_1: 0.20,
            Zone.ZONE_2: 0.40,
            Zone.ZONE_3: 0.60,
            Zone.ZONE_4: 0.80,
            Zone.ZONE_5: 0.98,
        }
        return ranges[self]
