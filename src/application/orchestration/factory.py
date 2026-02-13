"""Orchestration factory for dependency injection.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import logging
from typing import Dict, Optional, Type, TypeVar

from src.application.orchestration.bot_orchestrator import (
    BotOrchestrator,
    OrchestratorConfig,
)
from src.application.orchestration.event_bus import EventBus
from src.application.orchestration.health_checker import HealthChecker
from src.domain.entities.bot import Bot
from src.domain.services.position_service import PositionService
from src.domain.services.risk_service import RiskService
from src.infrastructure.repositories.bot_repository import BotRepository

logger = logging.getLogger(__name__)

T = TypeVar("T")


class OrchestratorFactory:
    """Factory for creating orchestrators with dependency injection.
    
    Manages:
    - Service registration and resolution
    - Singleton shared services (EventBus, HealthChecker)
    - Orchestrator lifecycle coordination
    
    Examples:
        >>> factory = OrchestratorFactory()
        >>> 
        >>> # Register shared services
        >>> factory.register_singleton(EventBus, event_bus_instance)
        >>> factory.register_singleton(HealthChecker, health_checker_instance)
        >>> 
        >>> # Register per-bot services
        >>> factory.register(BotRepository, bot_repository_instance)
        >>> factory.register(PositionService, position_service_instance)
        >>> factory.register(RiskService, risk_service_instance)
        >>> 
        >>> # Create orchestrator for bot
        >>> orchestrator = factory.create_orchestrator(bot)
    """

    def __init__(self) -> None:
        """Initialize factory."""
        self._singletons: Dict[Type, any] = {}
        self._services: Dict[Type, any] = {}
        self._orchestrators: Dict[int, BotOrchestrator] = {}  # bot_id -> orchestrator

    def register_singleton(self, service_type: Type[T], instance: T) -> None:
        """Register singleton service.
        
        Args:
            service_type: Service type (class)
            instance: Service instance (shared across orchestrators)
        
        Examples:
            >>> event_bus = EventBus()
            >>> factory.register_singleton(EventBus, event_bus)
        """
        self._singletons[service_type] = instance
        logger.info(f"Registered singleton: {service_type.__name__}")

    def register(self, service_type: Type[T], instance: T) -> None:
        """Register service instance.
        
        Args:
            service_type: Service type (class)
            instance: Service instance
        
        Examples:
            >>> bot_repo = BotRepository(db_session)
            >>> factory.register(BotRepository, bot_repo)
        """
        self._services[service_type] = instance
        logger.info(f"Registered service: {service_type.__name__}")

    def resolve(self, service_type: Type[T]) -> T:
        """Resolve service instance.
        
        Args:
            service_type: Service type to resolve
        
        Returns:
            Service instance
        
        Raises:
            ValueError: If service not registered
        
        Examples:
            >>> event_bus = factory.resolve(EventBus)
        """
        # Check singletons first
        if service_type in self._singletons:
            return self._singletons[service_type]
        
        # Check services
        if service_type in self._services:
            return self._services[service_type]
        
        raise ValueError(
            f"Service not registered: {service_type.__name__}. "
            f"Available: {list(self._singletons.keys()) + list(self._services.keys())}"
        )

    def create_orchestrator(
        self,
        bot: Bot,
        config: Optional[OrchestratorConfig] = None,
    ) -> BotOrchestrator:
        """Create orchestrator for bot.
        
        Args:
            bot: Bot entity
            config: Orchestrator configuration (optional)
        
        Returns:
            Configured BotOrchestrator
        
        Raises:
            ValueError: If required services not registered
        
        Examples:
            >>> bot = Bot(bot_id=8, ...)
            >>> orchestrator = factory.create_orchestrator(bot)
        """
        # Check if orchestrator already exists
        if bot.bot_id in self._orchestrators:
            logger.warning(
                f"Orchestrator for bot {bot.bot_id} already exists, returning existing."
            )
            return self._orchestrators[bot.bot_id]
        
        # Resolve dependencies
        bot_repository = self.resolve(BotRepository)
        position_service = self.resolve(PositionService)
        risk_service = self.resolve(RiskService)
        
        # Create orchestrator
        orchestrator = BotOrchestrator(
            bot=bot,
            bot_repository=bot_repository,
            position_service=position_service,
            risk_service=risk_service,
            config=config or OrchestratorConfig(),
        )
        
        # Register orchestrator
        self._orchestrators[bot.bot_id] = orchestrator
        
        logger.info(f"Created orchestrator for bot {bot.bot_id}")
        
        return orchestrator

    def get_orchestrator(self, bot_id: int) -> Optional[BotOrchestrator]:
        """Get orchestrator for bot.
        
        Args:
            bot_id: Bot ID
        
        Returns:
            BotOrchestrator or None if not found
        """
        return self._orchestrators.get(bot_id)

    async def start_all(self) -> None:
        """Start all registered orchestrators."""
        logger.info("Starting all orchestrators")
        
        for bot_id, orchestrator in self._orchestrators.items():
            try:
                await orchestrator.start()
                logger.info(f"Started orchestrator for bot {bot_id}")
            except Exception as e:
                logger.error(
                    f"Failed to start orchestrator for bot {bot_id}",
                    exc_info=True,
                )

    async def stop_all(self) -> None:
        """Stop all registered orchestrators."""
        logger.info("Stopping all orchestrators")
        
        for bot_id, orchestrator in self._orchestrators.items():
            try:
                await orchestrator.stop()
                logger.info(f"Stopped orchestrator for bot {bot_id}")
            except Exception as e:
                logger.error(
                    f"Failed to stop orchestrator for bot {bot_id}",
                    exc_info=True,
                )
