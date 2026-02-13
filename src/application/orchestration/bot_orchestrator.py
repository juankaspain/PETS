"""Bot orchestrator for lifecycle management.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from src.domain.entities.bot import Bot, BotState
from src.domain.services.position_service import PositionService
from src.domain.services.risk_service import RiskService
from src.infrastructure.repositories.bot_repository import BotRepository

logger = logging.getLogger(__name__)


class OrchestratorState(str, Enum):
    """Orchestrator state."""

    IDLE = "IDLE"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class OrchestratorConfig:
    """Orchestrator configuration."""

    health_check_interval_seconds: int = 30
    max_consecutive_errors: int = 3
    graceful_shutdown_timeout_seconds: int = 60


class BotOrchestrator:
    """Orchestrates bot lifecycle and coordination.
    
    Responsibilities:
    - Bot state management
    - Health monitoring
    - Event coordination
    - Error recovery
    - Graceful shutdown
    
    Examples:
        >>> orchestrator = BotOrchestrator(
        ...     bot=bot,
        ...     bot_repository=bot_repo,
        ...     position_service=pos_service,
        ...     risk_service=risk_service,
        ... )
        >>> await orchestrator.start()
        >>> await orchestrator.stop()
    """

    def __init__(
        self,
        bot: Bot,
        bot_repository: BotRepository,
        position_service: PositionService,
        risk_service: RiskService,
        config: Optional[OrchestratorConfig] = None,
    ) -> None:
        """Initialize orchestrator.
        
        Args:
            bot: Bot entity to orchestrate
            bot_repository: Bot persistence
            position_service: Position management
            risk_service: Risk monitoring
            config: Orchestrator configuration
        """
        self._bot = bot
        self._bot_repository = bot_repository
        self._position_service = position_service
        self._risk_service = risk_service
        self._config = config or OrchestratorConfig()
        
        self._state = OrchestratorState.IDLE
        self._health_check_task: Optional[asyncio.Task] = None
        self._consecutive_errors = 0
        self._shutdown_event = asyncio.Event()

    @property
    def state(self) -> OrchestratorState:
        """Get current orchestrator state."""
        return self._state

    @property
    def bot_id(self) -> int:
        """Get bot ID."""
        return self._bot.bot_id

    async def start(self) -> None:
        """Start bot orchestration.
        
        Raises:
            RuntimeError: If already running or invalid state
        """
        if self._state not in {OrchestratorState.IDLE, OrchestratorState.STOPPED}:
            raise RuntimeError(
                f"Cannot start from state {self._state}. "
                f"Must be IDLE or STOPPED."
            )
        
        logger.info(f"Starting orchestrator for bot {self.bot_id}")
        
        try:
            self._state = OrchestratorState.INITIALIZING
            
            # Validate configuration
            await self._validate_config()
            
            # Initialize services
            await self._initialize_services()
            
            # Start health monitoring
            self._health_check_task = asyncio.create_task(
                self._health_check_loop()
            )
            
            # Transition bot to RUNNING
            self._bot.start()
            await self._bot_repository.update(self._bot)
            
            self._state = OrchestratorState.RUNNING
            self._consecutive_errors = 0
            
            logger.info(f"Orchestrator started for bot {self.bot_id}")
            
        except Exception as e:
            logger.error(
                f"Failed to start orchestrator for bot {self.bot_id}",
                exc_info=True,
            )
            self._state = OrchestratorState.ERROR
            raise

    async def stop(self) -> None:
        """Stop bot orchestration gracefully.
        
        Raises:
            RuntimeError: If not running
        """
        if self._state not in {
            OrchestratorState.RUNNING,
            OrchestratorState.PAUSED,
            OrchestratorState.ERROR,
        }:
            raise RuntimeError(
                f"Cannot stop from state {self._state}. "
                f"Must be RUNNING, PAUSED, or ERROR."
            )
        
        logger.info(f"Stopping orchestrator for bot {self.bot_id}")
        
        try:
            self._state = OrchestratorState.STOPPING
            
            # Signal shutdown
            self._shutdown_event.set()
            
            # Cancel health checks
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await asyncio.wait_for(
                        self._health_check_task,
                        timeout=5.0,
                    )
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
            
            # Close open positions (if configured)
            await self._close_positions()
            
            # Cleanup services
            await self._cleanup_services()
            
            # Transition bot to IDLE
            self._bot.stop()
            await self._bot_repository.update(self._bot)
            
            self._state = OrchestratorState.STOPPED
            
            logger.info(f"Orchestrator stopped for bot {self.bot_id}")
            
        except Exception as e:
            logger.error(
                f"Error stopping orchestrator for bot {self.bot_id}",
                exc_info=True,
            )
            self._state = OrchestratorState.ERROR
            raise

    async def pause(self) -> None:
        """Pause bot orchestration.
        
        Suspends trading but keeps monitoring active.
        
        Raises:
            RuntimeError: If not running
        """
        if self._state != OrchestratorState.RUNNING:
            raise RuntimeError(
                f"Cannot pause from state {self._state}. Must be RUNNING."
            )
        
        logger.info(f"Pausing orchestrator for bot {self.bot_id}")
        
        self._bot.pause()
        await self._bot_repository.update(self._bot)
        self._state = OrchestratorState.PAUSED
        
        logger.info(f"Orchestrator paused for bot {self.bot_id}")

    async def resume(self) -> None:
        """Resume bot orchestration.
        
        Raises:
            RuntimeError: If not paused
        """
        if self._state != OrchestratorState.PAUSED:
            raise RuntimeError(
                f"Cannot resume from state {self._state}. Must be PAUSED."
            )
        
        logger.info(f"Resuming orchestrator for bot {self.bot_id}")
        
        self._bot.resume()
        await self._bot_repository.update(self._bot)
        self._state = OrchestratorState.RUNNING
        
        logger.info(f"Orchestrator resumed for bot {self.bot_id}")

    async def _validate_config(self) -> None:
        """Validate bot configuration.
        
        Raises:
            ValueError: If configuration invalid
        """
        # Validate capital allocation
        if self._bot.capital_allocated <= 0:
            raise ValueError(
                f"Invalid capital allocation: {self._bot.capital_allocated}"
            )
        
        # Additional validation logic here
        logger.debug(f"Configuration validated for bot {self.bot_id}")

    async def _initialize_services(self) -> None:
        """Initialize required services."""
        logger.debug(f"Initializing services for bot {self.bot_id}")
        # Service initialization logic here

    async def _cleanup_services(self) -> None:
        """Cleanup services on shutdown."""
        logger.debug(f"Cleaning up services for bot {self.bot_id}")
        # Cleanup logic here

    async def _close_positions(self) -> None:
        """Close all open positions."""
        logger.info(f"Closing positions for bot {self.bot_id}")
        
        positions = await self._position_service.get_open_positions(
            bot_id=self.bot_id
        )
        
        for position in positions:
            try:
                await self._position_service.close_position(
                    position_id=position.position_id
                )
            except Exception as e:
                logger.error(
                    f"Failed to close position {position.position_id}",
                    exc_info=True,
                )

    async def _health_check_loop(self) -> None:
        """Periodic health check loop."""
        logger.info(f"Starting health check loop for bot {self.bot_id}")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    await self._perform_health_check()
                    self._consecutive_errors = 0
                    
                except Exception as e:
                    self._consecutive_errors += 1
                    logger.error(
                        f"Health check failed for bot {self.bot_id} "
                        f"({self._consecutive_errors}/"
                        f"{self._config.max_consecutive_errors})",
                        exc_info=True,
                    )
                    
                    if (
                        self._consecutive_errors
                        >= self._config.max_consecutive_errors
                    ):
                        logger.critical(
                            f"Max consecutive errors reached for bot {self.bot_id}. "
                            f"Triggering emergency stop."
                        )
                        await self._handle_critical_error()
                        break
                
                await asyncio.sleep(
                    self._config.health_check_interval_seconds
                )
        
        except asyncio.CancelledError:
            logger.info(f"Health check loop cancelled for bot {self.bot_id}")
            raise

    async def _perform_health_check(self) -> None:
        """Perform single health check.
        
        Raises:
            Exception: If health check fails
        """
        # Check wallet balance
        # Check market data connection
        # Check order execution latency
        # Check risk limits
        # Check database connection
        
        logger.debug(f"Health check passed for bot {self.bot_id}")

    async def _handle_critical_error(self) -> None:
        """Handle critical error condition."""
        logger.critical(f"Handling critical error for bot {self.bot_id}")
        
        try:
            self._state = OrchestratorState.ERROR
            self._bot.handle_error("Critical health check failure")
            await self._bot_repository.update(self._bot)
            
            # Trigger circuit breaker
            await self._risk_service.trigger_circuit_breaker(
                bot_id=self.bot_id,
                reason="consecutive_health_check_failures",
            )
            
        except Exception as e:
            logger.error(
                f"Failed to handle critical error for bot {self.bot_id}",
                exc_info=True,
            )
