"""Bot Manager - Orchestrates all trading bots in the PETS system.

This module provides centralized management for:
- Bot lifecycle (start, stop, pause, resume)
- Configuration loading and validation
- Health monitoring and metrics collection
- Graceful shutdown handling
"""

import asyncio
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Type
from dataclasses import dataclass, field
from datetime import datetime

from .base_bot import BaseBotStrategy, BotState, BotMetrics

logger = logging.getLogger(__name__)


@dataclass
class BotRegistry:
    """Registry entry for a managed bot."""
    bot_id: int
    strategy_type: str
    bot_instance: Optional[BaseBotStrategy] = None
    config_path: Optional[Path] = None
    config: Dict = field(default_factory=dict)
    enabled: bool = True
    last_health_check: Optional[datetime] = None


class BotManager:
    """Centralized manager for all trading bots.
    
    Responsibilities:
    - Load bot configurations from configs/ directory
    - Instantiate and manage bot lifecycles
    - Monitor bot health and collect metrics
    - Handle graceful shutdown of all bots
    
    Example usage:
        manager = BotManager(configs_dir="configs/")
        await manager.load_configs()
        await manager.start_all()
        # ... run trading session ...
        await manager.stop_all()
    """
    
    def __init__(self, configs_dir: str = "configs/"):
        self.configs_dir = Path(configs_dir)
        self._bots: Dict[int, BotRegistry] = {}
        self._running = False
        self._health_check_interval = 30  # seconds
        self._health_task: Optional[asyncio.Task] = None
        
    async def load_configs(self) -> int:
        """Load all bot configurations from the configs directory.
        
        Returns:
            Number of configurations loaded successfully.
        """
        loaded = 0
        config_files = sorted(self.configs_dir.glob("bot_*.yaml"))
        
        for config_path in config_files:
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                bot_id = config.get('bot_id')
                if bot_id is None:
                    logger.warning(f"Config {config_path} missing bot_id, skipping")
                    continue
                
                self._bots[bot_id] = BotRegistry(
                    bot_id=bot_id,
                    strategy_type=config.get('strategy_type', 'unknown'),
                    config_path=config_path,
                    config=config,
                    enabled=config.get('enabled', True)
                )
                loaded += 1
                logger.info(f"Loaded config for Bot {bot_id}: {config_path.name}")
                
            except Exception as e:
                logger.error(f"Failed to load {config_path}: {e}")
                
        logger.info(f"Loaded {loaded} bot configurations")
        return loaded
    
    def register_bot_class(self, bot_id: int, bot_class: Type[BaseBotStrategy]) -> None:
        """Register a bot class for instantiation.
        
        Args:
            bot_id: The bot ID to register
            bot_class: The bot strategy class to instantiate
        """
        if bot_id not in self._bots:
            logger.warning(f"No config found for bot_id {bot_id}")
            return
            
        registry = self._bots[bot_id]
        registry.bot_instance = bot_class(registry.config)
        logger.info(f"Registered Bot {bot_id} with class {bot_class.__name__}")
    
    async def start_bot(self, bot_id: int) -> bool:
        """Start a specific bot."""
        if bot_id not in self._bots:
            logger.error(f"Bot {bot_id} not found")
            return False
            
        registry = self._bots[bot_id]
        if not registry.enabled:
            logger.info(f"Bot {bot_id} is disabled, skipping")
            return False
            
        if registry.bot_instance is None:
            logger.error(f"Bot {bot_id} has no registered instance")
            return False
            
        try:
            await registry.bot_instance.start()
            logger.info(f"Started Bot {bot_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to start Bot {bot_id}: {e}")
            return False
    
    async def stop_bot(self, bot_id: int) -> bool:
        """Stop a specific bot gracefully."""
        if bot_id not in self._bots:
            return False
            
        registry = self._bots[bot_id]
        if registry.bot_instance is None:
            return False
            
        try:
            await registry.bot_instance.stop_gracefully()
            logger.info(f"Stopped Bot {bot_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop Bot {bot_id}: {e}")
            return False
    
    async def start_all(self) -> Dict[int, bool]:
        """Start all enabled bots.
        
        Returns:
            Dict mapping bot_id to start success status.
        """
        self._running = True
        results = {}
        
        for bot_id in sorted(self._bots.keys()):
            results[bot_id] = await self.start_bot(bot_id)
            
        # Start health monitoring
        self._health_task = asyncio.create_task(self._health_monitor_loop())
        
        started = sum(1 for v in results.values() if v)
        logger.info(f"Started {started}/{len(results)} bots")
        return results
    
    async def stop_all(self) -> None:
        """Stop all running bots gracefully."""
        self._running = False
        
        # Cancel health monitoring
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
        
        # Stop all bots in reverse order
        for bot_id in sorted(self._bots.keys(), reverse=True):
            await self.stop_bot(bot_id)
            
        logger.info("All bots stopped")
    
    def get_metrics(self) -> List[BotMetrics]:
        """Collect metrics from all bots."""
        metrics = []
        for registry in self._bots.values():
            if registry.bot_instance:
                metrics.append(registry.bot_instance.get_metrics())
        return metrics
    
    def get_bot_status(self, bot_id: int) -> Optional[BotState]:
        """Get the current state of a specific bot."""
        if bot_id not in self._bots:
            return None
        registry = self._bots[bot_id]
        if registry.bot_instance:
            return registry.bot_instance.state
        return BotState.IDLE
    
    async def _health_monitor_loop(self) -> None:
        """Background task to monitor bot health."""
        while self._running:
            try:
                await asyncio.sleep(self._health_check_interval)
                await self._check_all_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def _check_all_health(self) -> None:
        """Check health of all running bots."""
        now = datetime.utcnow()
        for bot_id, registry in self._bots.items():
            if registry.bot_instance and registry.bot_instance.state == BotState.ACTIVE:
                registry.last_health_check = now
                # Check for error state
                if registry.bot_instance.state == BotState.ERROR:
                    logger.warning(f"Bot {bot_id} in ERROR state")
    
    @property
    def bot_count(self) -> int:
        """Number of registered bots."""
        return len(self._bots)
    
    @property
    def active_count(self) -> int:
        """Number of currently active bots."""
        return sum(
            1 for r in self._bots.values()
            if r.bot_instance and r.bot_instance.state == BotState.ACTIVE
        )
    
    def __repr__(self) -> str:
        return f"BotManager(bots={self.bot_count}, active={self.active_count})"
