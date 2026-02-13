"""Graceful degradation strategies.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, Optional, TypeVar

from src.application.orchestration.health_checker import HealthStatus

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class DegradationConfig:
    """Degradation configuration."""

    enable_fallback: bool = True
    cache_ttl_seconds: int = 300
    health_threshold: HealthStatus = HealthStatus.DEGRADED


class FallbackStrategy(ABC, Generic[T]):
    """Abstract fallback strategy."""

    @abstractmethod
    async def execute(self) -> T:
        """Execute fallback strategy.
        
        Returns:
            Fallback result
        """
        pass


class CacheFallback(FallbackStrategy[T]):
    """Fallback to cached value."""

    def __init__(self, cache_key: str, cache: Dict[str, Any]) -> None:
        """Initialize cache fallback.
        
        Args:
            cache_key: Key to lookup in cache
            cache: Cache dictionary
        """
        self._cache_key = cache_key
        self._cache = cache

    async def execute(self) -> T:
        """Get value from cache.
        
        Returns:
            Cached value
        
        Raises:
            KeyError: If key not in cache
        """
        logger.info(f"Using cached value for key: {self._cache_key}")
        return self._cache[self._cache_key]


class DefaultValueFallback(FallbackStrategy[T]):
    """Fallback to default value."""

    def __init__(self, default_value: T) -> None:
        """Initialize default value fallback.
        
        Args:
            default_value: Default value to return
        """
        self._default_value = default_value

    async def execute(self) -> T:
        """Return default value.
        
        Returns:
            Default value
        """
        logger.info("Using default fallback value")
        return self._default_value


class GracefulDegradation(Generic[T]):
    """Graceful degradation wrapper.
    
    Executes primary operation, falls back to degraded mode on failure.
    
    Examples:
        >>> async def primary_api_call() -> dict:
        ...     return await external_api.get_data()
        >>> 
        >>> degradation = GracefulDegradation(
        ...     primary_fn=primary_api_call,
        ...     fallback=DefaultValueFallback({}),
        ... )
        >>> 
        >>> result = await degradation.execute()
    """

    def __init__(
        self,
        primary_fn: Callable[..., T],
        fallback: FallbackStrategy[T],
        config: Optional[DegradationConfig] = None,
    ) -> None:
        """Initialize graceful degradation.
        
        Args:
            primary_fn: Primary async function to execute
            fallback: Fallback strategy on failure
            config: Degradation configuration
        """
        self._primary_fn = primary_fn
        self._fallback = fallback
        self._config = config or DegradationConfig()

    async def execute(self, *args: Any, **kwargs: Any) -> T:
        """Execute with graceful degradation.
        
        Args:
            *args: Positional arguments for primary function
            **kwargs: Keyword arguments for primary function
        
        Returns:
            Primary result or fallback result
        """
        try:
            return await self._primary_fn(*args, **kwargs)
        
        except Exception as e:
            logger.warning(
                f"Primary operation failed, using fallback. Error: {e}",
                exc_info=True,
            )
            
            if self._config.enable_fallback:
                return await self._fallback.execute()
            else:
                raise
