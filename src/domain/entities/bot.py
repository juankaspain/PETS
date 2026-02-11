"""Bot entity - Trading bot with state machine."""

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.domain.exceptions import DomainError
from src.domain.value_objects.enums import BotState


@dataclass(frozen=True)
class Bot:
    """Trading bot entity.

    Represents a single trading bot with strategy configuration.
    Bot has state machine for lifecycle management.

    Attributes:
        bot_id: Unique bot identifier (1-10)
        name: Human-readable bot name
        strategy_type: Strategy type (e.g., 'tail_risk', 'market_making')
        state: Current bot state
        config: Strategy-specific configuration dict
        capital_allocated: Capital allocated to this bot (USDC)
        created_at: Bot creation timestamp
        started_at: Last start timestamp (None if never started)
        stopped_at: Last stop timestamp (None if never stopped)
    """

    bot_id: int
    name: str
    strategy_type: str
    state: BotState
    config: dict[str, Any]
    capital_allocated: Decimal
    created_at: datetime
    started_at: datetime | None = None
    stopped_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate bot attributes.

        Raises:
            DomainError: If validation fails
        """
        if not 1 <= self.bot_id <= 10:
            raise DomainError(f"Invalid bot_id: {self.bot_id}", valid_range="1-10")

        if self.capital_allocated < Decimal("0"):
            raise DomainError(
                f"Capital cannot be negative: {self.capital_allocated}"
            )

        if not self.name.strip():
            raise DomainError("Bot name cannot be empty")

        if not self.strategy_type.strip():
            raise DomainError("Strategy type cannot be empty")

    def start(self, timestamp: datetime) -> "Bot":
        """Start bot.

        Args:
            timestamp: Start timestamp

        Returns:
            New Bot instance in STARTING state

        Raises:
            DomainError: If bot cannot be started from current state
        """
        if not self.state.can_start:
            raise DomainError(
                f"Cannot start bot in state {self.state}",
                bot_id=self.bot_id,
                current_state=self.state.value,
            )

        return replace(self, state=BotState.STARTING, started_at=timestamp)

    def activate(self) -> "Bot":
        """Activate bot (transition from STARTING to ACTIVE).

        Returns:
            New Bot instance in ACTIVE state

        Raises:
            DomainError: If bot not in STARTING state
        """
        if self.state != BotState.STARTING:
            raise DomainError(
                f"Can only activate from STARTING state, current: {self.state}",
                bot_id=self.bot_id,
            )

        return replace(self, state=BotState.ACTIVE)

    def pause(self) -> "Bot":
        """Pause bot.

        Returns:
            New Bot instance in PAUSED state

        Raises:
            DomainError: If bot cannot be paused from current state
        """
        if not self.state.can_pause:
            raise DomainError(
                f"Cannot pause bot in state {self.state}",
                bot_id=self.bot_id,
                current_state=self.state.value,
            )

        return replace(self, state=BotState.PAUSED)

    def resume(self) -> "Bot":
        """Resume bot from paused state.

        Returns:
            New Bot instance in ACTIVE state

        Raises:
            DomainError: If bot cannot be resumed from current state
        """
        if not self.state.can_resume:
            raise DomainError(
                f"Cannot resume bot in state {self.state}",
                bot_id=self.bot_id,
                current_state=self.state.value,
            )

        return replace(self, state=BotState.ACTIVE)

    def stop(self, timestamp: datetime) -> "Bot":
        """Stop bot gracefully.

        Args:
            timestamp: Stop timestamp

        Returns:
            New Bot instance in STOPPING state

        Raises:
            DomainError: If bot cannot be stopped from current state
        """
        if not self.state.can_stop:
            raise DomainError(
                f"Cannot stop bot in state {self.state}",
                bot_id=self.bot_id,
                current_state=self.state.value,
            )

        return replace(self, state=BotState.STOPPING, stopped_at=timestamp)

    def mark_stopped(self) -> "Bot":
        """Mark bot as stopped (transition from STOPPING to STOPPED).

        Returns:
            New Bot instance in STOPPED state

        Raises:
            DomainError: If bot not in STOPPING state
        """
        if self.state != BotState.STOPPING:
            raise DomainError(
                f"Can only mark stopped from STOPPING state, current: {self.state}",
                bot_id=self.bot_id,
            )

        return replace(self, state=BotState.STOPPED)

    def mark_error(self, error_message: str) -> "Bot":
        """Mark bot as in error state.

        Args:
            error_message: Error description

        Returns:
            New Bot instance in ERROR state with error in config
        """
        new_config = {**self.config, "last_error": error_message}
        return replace(self, state=BotState.ERROR, config=new_config)

    def emergency_halt(self, reason: str) -> "Bot":
        """Emergency halt bot.

        Args:
            reason: Halt reason

        Returns:
            New Bot instance in EMERGENCY_HALT state
        """
        new_config = {**self.config, "halt_reason": reason}
        return replace(self, state=BotState.EMERGENCY_HALT, config=new_config)

    def update_config(self, config: dict[str, Any]) -> "Bot":
        """Update bot configuration.

        Args:
            config: New configuration dict

        Returns:
            New Bot instance with updated config

        Raises:
            DomainError: If bot is running (must pause first)
        """
        if self.state == BotState.ACTIVE:
            raise DomainError(
                "Cannot update config while bot is active",
                bot_id=self.bot_id,
                hint="Pause bot first",
            )

        return replace(self, config=config)

    def update_capital(self, new_capital: Decimal) -> "Bot":
        """Update allocated capital.

        Args:
            new_capital: New capital allocation

        Returns:
            New Bot instance with updated capital

        Raises:
            DomainError: If new_capital negative or bot is active
        """
        if new_capital < Decimal("0"):
            raise DomainError(f"Capital cannot be negative: {new_capital}")

        if self.state == BotState.ACTIVE:
            raise DomainError(
                "Cannot update capital while bot is active",
                bot_id=self.bot_id,
                hint="Pause bot first",
            )

        return replace(self, capital_allocated=new_capital)

    @property
    def is_running(self) -> bool:
        """Check if bot is running (ACTIVE or PAUSED)."""
        return self.state.is_running

    def __str__(self) -> str:
        """String representation."""
        return f"Bot {self.bot_id}: {self.name} ({self.state.value})"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"Bot(bot_id={self.bot_id}, name='{self.name}', "
            f"strategy='{self.strategy_type}', state={self.state})"
        )
