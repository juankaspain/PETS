"""Bot entity with state machine."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class BotState(str, Enum):
    """Bot state machine states."""

    IDLE = "IDLE"  # Waiting for opportunities
    ANALYZING = "ANALYZING"  # Analyzing market conditions
    PLACING = "PLACING"  # Placing orders
    HOLDING = "HOLDING"  # Holding positions
    EXITING = "EXITING"  # Exiting positions
    STOPPED = "STOPPED"  # Stopped (circuit breaker or manual)
    ERROR = "ERROR"  # Error state


@dataclass(frozen=True)
class Bot:
    """Bot entity.

    Represents a trading bot with strategy configuration and state.

    Example:
        >>> bot = Bot(
        ...     bot_id=1,
        ...     strategy_type="VOLATILITY_SKEW",
        ...     state=BotState.IDLE,
        ...     config={"threshold": 0.15, "hold_hours": 24},
        ...     capital_allocated=Decimal("10000"),
        ... )
    """

    bot_id: int
    strategy_type: str
    state: BotState
    config: dict
    capital_allocated: Decimal
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Validate bot."""
        if self.capital_allocated < Decimal("0"):
            raise ValueError("capital_allocated must be non-negative")

        if not self.strategy_type:
            raise ValueError("strategy_type is required")

    def can_transition_to(self, new_state: BotState) -> bool:
        """Check if state transition is valid.

        Args:
            new_state: Target state

        Returns:
            True if transition is valid

        Valid transitions:
        - IDLE → ANALYZING, STOPPED
        - ANALYZING → PLACING, IDLE, ERROR
        - PLACING → HOLDING, IDLE, ERROR
        - HOLDING → EXITING, ERROR
        - EXITING → IDLE, ERROR
        - STOPPED → IDLE
        - ERROR → IDLE
        """
        valid_transitions = {
            BotState.IDLE: {BotState.ANALYZING, BotState.STOPPED},
            BotState.ANALYZING: {BotState.PLACING, BotState.IDLE, BotState.ERROR},
            BotState.PLACING: {BotState.HOLDING, BotState.IDLE, BotState.ERROR},
            BotState.HOLDING: {BotState.EXITING, BotState.ERROR},
            BotState.EXITING: {BotState.IDLE, BotState.ERROR},
            BotState.STOPPED: {BotState.IDLE},
            BotState.ERROR: {BotState.IDLE},
        }

        return new_state in valid_transitions.get(self.state, set())
