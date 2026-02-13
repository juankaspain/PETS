"""Retry policy for resilient operations.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import asyncio
import functools
import logging
import random
from dataclasses import dataclass
from typing import Any, Callable, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class RetryConfig:
    """Retry configuration."""

    max_attempts: int = 3
    base_delay_seconds: float = 2.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    jitter_percent: float = 0.2
    timeout_seconds: Optional[float] = None


class RetryableError(Exception):
    """Error that should trigger retry."""

    pass


class TerminalError(Exception):
    """Error that should not be retried."""

    pass


def is_retryable_error(error: Exception) -> bool:
    """Determine if error is retryable.
    
    Args:
        error: Exception to check
    
    Returns:
        True if error should trigger retry
    
    Examples:
        >>> is_retryable_error(ConnectionError())
        True
        >>> is_retryable_error(ValueError())
        False
    """
    # Network/transient errors
    retryable_types = (
        ConnectionError,
        TimeoutError,
        asyncio.TimeoutError,
        RetryableError,
    )
    
    # Terminal errors
    terminal_types = (
        ValueError,
        TypeError,
        KeyError,
        TerminalError,
    )
    
    if isinstance(error, terminal_types):
        return False
    
    if isinstance(error, retryable_types):
        return True
    
    # Default: retry unknown errors
    return True


def calculate_delay(
    attempt: int,
    config: RetryConfig,
) -> float:
    """Calculate retry delay with exponential backoff and jitter.
    
    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration
    
    Returns:
        Delay in seconds
    
    Examples:
        >>> config = RetryConfig()
        >>> calculate_delay(0, config)  # ~2.0s ± jitter
        >>> calculate_delay(1, config)  # ~4.0s ± jitter
        >>> calculate_delay(2, config)  # ~8.0s ± jitter
    """
    # Exponential backoff
    delay = config.base_delay_seconds * (config.exponential_base ** attempt)
    
    # Cap at max delay
    delay = min(delay, config.max_delay_seconds)
    
    # Add jitter to prevent thundering herd
    jitter = delay * config.jitter_percent
    delay += random.uniform(-jitter, jitter)
    
    return max(0, delay)


async def retry(
    func: Callable[..., T],
    *args: Any,
    config: Optional[RetryConfig] = None,
    **kwargs: Any,
) -> T:
    """Execute function with retry logic.
    
    Args:
        func: Async function to execute
        *args: Positional arguments for func
        config: Retry configuration (uses defaults if None)
        **kwargs: Keyword arguments for func
    
    Returns:
        Function result
    
    Raises:
        Exception: Last exception if all attempts fail
    
    Examples:
        >>> async def flaky_api_call():
        ...     # May fail with ConnectionError
        ...     return "success"
        >>> 
        >>> result = await retry(
        ...     flaky_api_call,
        ...     config=RetryConfig(max_attempts=5),
        ... )
    """
    cfg = config or RetryConfig()
    last_exception: Optional[Exception] = None
    
    for attempt in range(cfg.max_attempts):
        try:
            if cfg.timeout_seconds:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=cfg.timeout_seconds,
                )
            else:
                return await func(*args, **kwargs)
        
        except Exception as e:
            last_exception = e
            
            # Check if retryable
            if not is_retryable_error(e):
                logger.error(
                    f"Terminal error in {func.__name__}, not retrying",
                    exc_info=True,
                )
                raise
            
            # Last attempt?
            if attempt == cfg.max_attempts - 1:
                logger.error(
                    f"Max retry attempts ({cfg.max_attempts}) reached "
                    f"for {func.__name__}",
                    exc_info=True,
                )
                raise
            
            # Calculate delay and retry
            delay = calculate_delay(attempt, cfg)
            logger.warning(
                f"Attempt {attempt + 1}/{cfg.max_attempts} failed for "
                f"{func.__name__}. Retrying in {delay:.2f}s. Error: {e}"
            )
            
            await asyncio.sleep(delay)
    
    # Should never reach here, but satisfy type checker
    if last_exception:
        raise last_exception
    
    raise RuntimeError("Retry logic error: no exception but no success")


def with_retry(config: Optional[RetryConfig] = None) -> Callable:
    """Decorator to add retry logic to async functions.
    
    Args:
        config: Retry configuration (uses defaults if None)
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry(config=RetryConfig(max_attempts=5))
        ... async def fetch_market_data():
        ...     # May fail with transient errors
        ...     return data
    """
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry(func, *args, config=config, **kwargs)
        
        return wrapper
    
    return decorator
