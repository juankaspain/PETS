"""Tests for retry policy.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import pytest

from src.application.orchestration.retry_policy import (
    RetryConfig,
    RetryableError,
    TerminalError,
    calculate_delay,
    is_retryable_error,
    retry,
    with_retry,
)


def test_is_retryable_error():
    """Test error classification."""
    # Retryable
    assert is_retryable_error(ConnectionError())
    assert is_retryable_error(TimeoutError())
    assert is_retryable_error(RetryableError())
    
    # Terminal
    assert not is_retryable_error(ValueError())
    assert not is_retryable_error(TypeError())
    assert not is_retryable_error(TerminalError())


def test_calculate_delay():
    """Test delay calculation."""
    config = RetryConfig(
        base_delay_seconds=2.0,
        exponential_base=2.0,
        max_delay_seconds=60.0,
        jitter_percent=0.2,
    )
    
    # First attempt: ~2s
    delay0 = calculate_delay(0, config)
    assert 1.6 <= delay0 <= 2.4  # 2.0 ± 20%
    
    # Second attempt: ~4s
    delay1 = calculate_delay(1, config)
    assert 3.2 <= delay1 <= 4.8  # 4.0 ± 20%
    
    # High attempt: capped at max
    delay_high = calculate_delay(10, config)
    assert delay_high <= config.max_delay_seconds * 1.2


@pytest.mark.asyncio
async def test_retry_success_first_attempt():
    """Test successful execution on first attempt."""
    call_count = 0
    
    async def always_succeeds():
        nonlocal call_count
        call_count += 1
        return "success"
    
    result = await retry(always_succeeds)
    
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_success_after_failures():
    """Test successful execution after retries."""
    call_count = 0
    
    async def succeeds_on_third_attempt():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Transient error")
        return "success"
    
    config = RetryConfig(
        max_attempts=3,
        base_delay_seconds=0.01,  # Fast tests
    )
    
    result = await retry(succeeds_on_third_attempt, config=config)
    
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_terminal_error():
    """Test terminal error not retried."""
    call_count = 0
    
    async def raises_terminal_error():
        nonlocal call_count
        call_count += 1
        raise ValueError("Terminal error")
    
    with pytest.raises(ValueError):
        await retry(raises_terminal_error)
    
    assert call_count == 1  # Not retried


@pytest.mark.asyncio
async def test_retry_max_attempts():
    """Test max attempts exhausted."""
    call_count = 0
    
    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise ConnectionError("Persistent error")
    
    config = RetryConfig(
        max_attempts=3,
        base_delay_seconds=0.01,
    )
    
    with pytest.raises(ConnectionError):
        await retry(always_fails, config=config)
    
    assert call_count == 3


@pytest.mark.asyncio
async def test_with_retry_decorator():
    """Test retry decorator."""
    call_count = 0
    
    @with_retry(config=RetryConfig(max_attempts=3, base_delay_seconds=0.01))
    async def decorated_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionError()
        return "success"
    
    result = await decorated_function()
    
    assert result == "success"
    assert call_count == 2
