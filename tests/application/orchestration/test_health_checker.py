"""Tests for health checker.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import pytest

from src.application.orchestration.health_checker import (
    HealthCheckResult,
    HealthChecker,
    HealthStatus,
)


@pytest.fixture
def health_checker():
    """Create health checker instance."""
    return HealthChecker()


@pytest.mark.asyncio
async def test_register_and_check(health_checker):
    """Test register and execute health check."""
    
    async def check_component():
        return HealthCheckResult(
            component="test_component",
            status=HealthStatus.HEALTHY,
            message="All good",
        )
    
    health_checker.register("test_component", check_component)
    
    status = await health_checker.check_all()
    
    assert status.is_healthy
    assert "test_component" in status.components
    assert status.components["test_component"].status == HealthStatus.HEALTHY


@pytest.mark.asyncio
async def test_unhealthy_component(health_checker):
    """Test unhealthy component detection."""
    
    async def check_unhealthy():
        return HealthCheckResult(
            component="unhealthy",
            status=HealthStatus.UNHEALTHY,
            message="Component down",
        )
    
    health_checker.register("unhealthy", check_unhealthy)
    
    status = await health_checker.check_all()
    
    assert not status.is_healthy
    assert status.overall_status == HealthStatus.UNHEALTHY


@pytest.mark.asyncio
async def test_degraded_status(health_checker):
    """Test degraded status aggregation."""
    
    async def check_healthy():
        return HealthCheckResult(
            component="healthy",
            status=HealthStatus.HEALTHY,
        )
    
    async def check_degraded():
        return HealthCheckResult(
            component="degraded",
            status=HealthStatus.DEGRADED,
            message="Slow response",
        )
    
    health_checker.register("healthy", check_healthy)
    health_checker.register("degraded", check_degraded)
    
    status = await health_checker.check_all()
    
    assert status.overall_status == HealthStatus.DEGRADED


@pytest.mark.asyncio
async def test_check_component_exception(health_checker):
    """Test exception handling in health check."""
    
    async def check_exception():
        raise ValueError("Simulated error")
    
    health_checker.register("exception", check_exception)
    
    status = await health_checker.check_all()
    
    assert "exception" in status.components
    assert status.components["exception"].status == HealthStatus.UNHEALTHY
