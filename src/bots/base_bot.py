"""Base bot strategy abstract class.

All trading bots must inherit from BaseBotStrategy and implement
the abstract methods: initialize, execute_cycle, stop_gracefully.

State machine:
    IDLE → STARTING → ACTIVE ⇄ PAUSED → STOPPING → STOPPED/ERROR
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BotState(str, Enum):
    """Bot state."""

    IDLE = "IDLE"  # Not started
    STARTING = "STARTING"  # Initializing
    ACTIVE = "ACTIVE"  # Running normally
    PAUSED = "PAUSED"  # Temporarily stopped
    STOPPING = "STOPPING"  # Shutting down
    STOPPED = "STOPPED"  # Cleanly stopped
    ERROR = "ERROR"  # Error state
    EMERGENCY_HALT = "EMERGENCY_HALT"  # Circuit breaker triggered


@dataclass
class BotMetrics:
    """Bot runtime metrics."""

    bot_id: int
    strategy_type: str
    state: BotState
    uptime_seconds: float
    cycles_completed: int
    errors_count: int
    last_cycle_duration_ms: float
    orders_placed: int
    positions_opened: int
    capital_allocated: float
    current_pnl: float
    last_update: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON logging."""
        return {
            "bot_id": self.bot_id,
            "strategy_type": self.strategy_type,
            "state": self.state.value,
            "uptime_seconds": self.uptime_seconds,
            "cycles_completed": self.cycles_completed,
            "errors_count": self.errors_count,
            "last_cycle_duration_ms": self.last_cycle_duration_ms,
            "orders_placed": self.orders_placed,
            "positions_opened": self.positions_opened,
            "capital_allocated": self.capital_allocated,
            "current_pnl": self.current_pnl,
            "last_update": self.last_update.isoformat(),
        }


class BaseBotStrategy(ABC):
    """Base bot strategy abstract class.

    All trading bots must inherit from this class and implement:
    - initialize(): Setup bot resources
    - execute_cycle(): Main trading logic loop
    - stop_gracefully(): Cleanup resources

    Example:
        >>> class MyBot(BaseBotStrategy):
        ...     async def initialize(self) -> None:
        ...         await self.setup_websocket()
        ...
        ...     async def execute_cycle(self) -> None:
        ...         await self.scan_markets()
        ...         await self.place_orders()
        ...
        ...     async def stop_gracefully(self) -> None:
        ...         await self.close_websocket()
    """

    def __init__(
        self,
        bot_id: int,
        strategy_type: str,
        config: Dict[str, Any],
    ) -> None:
        """Initialize base bot.

        Args:
            bot_id: Unique bot identifier
            strategy_type: Strategy name (e.g., 'market_making')
            config: Bot configuration dict

        Raises:
            ValueError: If config validation fails
        """
        self.bot_id = bot_id
        self.strategy_type = strategy_type
        self.config = config

        # State management
        self._state: BotState = BotState.IDLE
        self._start_time: Optional[datetime] = None
        self._should_stop: bool = False
        self._task: Optional[asyncio.Task[None]] = None

        # Metrics
        self._cycles_completed: int = 0
        self._errors_count: int = 0
        self._last_cycle_duration_ms: float = 0.0
        self._orders_placed: int = 0
        self._positions_opened: int = 0
        self._current_pnl: float = 0.0

        # Validate config
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate bot configuration.

        Raises:
            ValueError: If config is invalid
        """
        required_keys = ["capital_allocated", "max_positions", "cycle_interval_seconds"]
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required config key: {key}")

        if self.config["capital_allocated"] <= 0:
            raise ValueError("capital_allocated must be > 0")

        if self.config["max_positions"] <= 0:
            raise ValueError("max_positions must be > 0")

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize bot resources.

        Called once when bot starts. Setup connections, load data, etc.

        Raises:
            Exception: If initialization fails
        """
        ...

    @abstractmethod
    async def execute_cycle(self) -> None:
        """Execute one trading cycle.

        Called repeatedly while bot is ACTIVE. Main trading logic goes here.

        Raises:
            Exception: If cycle fails
        """
        ...

    @abstractmethod
    async def stop_gracefully(self) -> None:
        """Stop bot gracefully.

        Called once when bot stops. Close connections, cleanup resources.

        Raises:
            Exception: If cleanup fails
        """
        ...

    async def start(self) -> None:
        """Start bot execution.

        Transitions: IDLE → STARTING → ACTIVE

        Raises:
            RuntimeError: If bot already running
        """
        if self._state != BotState.IDLE:
            raise RuntimeError(f"Cannot start bot in state {self._state}")

        logger.info(
            "bot_starting",
            extra={
                "bot_id": self.bot_id,
                "strategy_type": self.strategy_type,
                "capital_allocated": self.config["capital_allocated"],
            },
        )

        self._state = BotState.STARTING
        self._start_time = datetime.utcnow()
        self._should_stop = False

        try:
            # Initialize bot-specific resources
            await self.initialize()

            # Start main loop
            self._state = BotState.ACTIVE
            self._task = asyncio.create_task(self._run_loop())

            logger.info(
                "bot_started",
                extra={"bot_id": self.bot_id, "strategy_type": self.strategy_type},
            )

        except Exception as e:
            self._state = BotState.ERROR
            logger.error(
                "bot_start_failed",
                extra={
                    "bot_id": self.bot_id,
                    "strategy_type": self.strategy_type,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    async def _run_loop(self) -> None:
        """Main execution loop.

        Runs while state is ACTIVE and _should_stop is False.
        """
        cycle_interval = self.config["cycle_interval_seconds"]

        while self._state == BotState.ACTIVE and not self._should_stop:
            cycle_start = datetime.utcnow()

            try:
                # Execute one cycle
                await self.execute_cycle()

                self._cycles_completed += 1
                self._last_cycle_duration_ms = (
                    datetime.utcnow() - cycle_start
                ).total_seconds() * 1000

                logger.debug(
                    "bot_cycle_completed",
                    extra={
                        "bot_id": self.bot_id,
                        "cycle_number": self._cycles_completed,
                        "duration_ms": self._last_cycle_duration_ms,
                    },
                )

            except Exception as e:
                self._errors_count += 1
                logger.error(
                    "bot_cycle_error",
                    extra={
                        "bot_id": self.bot_id,
                        "cycle_number": self._cycles_completed,
                        "error": str(e),
                    },
                    exc_info=True,
                )

                # Emergency halt after 5 consecutive errors
                if self._errors_count >= 5:
                    await self.emergency_halt()
                    break

            # Wait before next cycle
            await asyncio.sleep(cycle_interval)

    async def pause(self) -> None:
        """Pause bot execution.

        Transitions: ACTIVE → PAUSED

        Raises:
            RuntimeError: If bot not ACTIVE
        """
        if self._state != BotState.ACTIVE:
            raise RuntimeError(f"Cannot pause bot in state {self._state}")

        self._state = BotState.PAUSED
        logger.info(
            "bot_paused", extra={"bot_id": self.bot_id, "strategy_type": self.strategy_type}
        )

    async def resume(self) -> None:
        """Resume bot execution.

        Transitions: PAUSED → ACTIVE

        Raises:
            RuntimeError: If bot not PAUSED
        """
        if self._state != BotState.PAUSED:
            raise RuntimeError(f"Cannot resume bot in state {self._state}")

        self._state = BotState.ACTIVE
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "bot_resumed", extra={"bot_id": self.bot_id, "strategy_type": self.strategy_type}
        )

    async def stop(self) -> None:
        """Stop bot gracefully.

        Transitions: ACTIVE/PAUSED → STOPPING → STOPPED

        Raises:
            RuntimeError: If bot not running
        """
        if self._state not in (BotState.ACTIVE, BotState.PAUSED):
            raise RuntimeError(f"Cannot stop bot in state {self._state}")

        logger.info(
            "bot_stopping", extra={"bot_id": self.bot_id, "strategy_type": self.strategy_type}
        )

        self._state = BotState.STOPPING
        self._should_stop = True

        # Wait for current cycle to finish
        if self._task and not self._task.done():
            try:
                await asyncio.wait_for(self._task, timeout=30.0)
            except asyncio.TimeoutError:
                logger.warning(
                    "bot_stop_timeout",
                    extra={"bot_id": self.bot_id, "strategy_type": self.strategy_type},
                )
                self._task.cancel()

        # Cleanup resources
        try:
            await self.stop_gracefully()
            self._state = BotState.STOPPED
            logger.info(
                "bot_stopped",
                extra={"bot_id": self.bot_id, "strategy_type": self.strategy_type},
            )
        except Exception as e:
            self._state = BotState.ERROR
            logger.error(
                "bot_stop_error",
                extra={
                    "bot_id": self.bot_id,
                    "strategy_type": self.strategy_type,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    async def emergency_halt(self) -> None:
        """Emergency halt bot immediately.

        Transitions: ANY → EMERGENCY_HALT

        Called by circuit breakers. Stops bot without cleanup.
        """
        logger.critical(
            "bot_emergency_halt",
            extra={
                "bot_id": self.bot_id,
                "strategy_type": self.strategy_type,
                "errors_count": self._errors_count,
            },
        )

        self._state = BotState.EMERGENCY_HALT
        self._should_stop = True

        if self._task and not self._task.done():
            self._task.cancel()

    def get_state(self) -> BotState:
        """Get current bot state.

        Returns:
            Current BotState
        """
        return self._state

    def get_metrics(self) -> BotMetrics:
        """Get bot runtime metrics.

        Returns:
            BotMetrics with current stats
        """
        uptime = 0.0
        if self._start_time:
            uptime = (datetime.utcnow() - self._start_time).total_seconds()

        return BotMetrics(
            bot_id=self.bot_id,
            strategy_type=self.strategy_type,
            state=self._state,
            uptime_seconds=uptime,
            cycles_completed=self._cycles_completed,
            errors_count=self._errors_count,
            last_cycle_duration_ms=self._last_cycle_duration_ms,
            orders_placed=self._orders_placed,
            positions_opened=self._positions_opened,
            capital_allocated=self.config["capital_allocated"],
            current_pnl=self._current_pnl,
        )

    def is_running(self) -> bool:
        """Check if bot is running.

        Returns:
            True if state is ACTIVE or PAUSED
        """
        return self._state in (BotState.ACTIVE, BotState.PAUSED)
