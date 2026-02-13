"""Health checker for system components.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Component health status."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class HealthCheckResult:
    """Health check result."""

    component: str
    status: HealthStatus
    message: Optional[str] = None
    latency_ms: Optional[float] = None
    timestamp: datetime = datetime.now()


@dataclass(frozen=True)
class CompositeHealthStatus:
    """Composite health status for all components."""

    overall_status: HealthStatus
    components: Dict[str, HealthCheckResult]
    timestamp: datetime

    @property
    def is_healthy(self) -> bool:
        """Check if all components healthy."""
        return self.overall_status == HealthStatus.HEALTHY


class HealthChecker:
    """Monitors health of system components.
    
    Components register health check functions that return HealthCheckResult.
    HealthChecker periodically executes checks and aggregates results.
    
    Examples:
        >>> checker = HealthChecker()
        >>> 
        >>> async def check_db() -> HealthCheckResult:
        ...     # Check database connection
        ...     return HealthCheckResult(
        ...         component="database",
        ...         status=HealthStatus.HEALTHY,
        ...     )
        >>> 
        >>> checker.register("database", check_db)
        >>> status = await checker.check_all()
        >>> print(status.is_healthy)
    """

    def __init__(self) -> None:
        """Initialize health checker."""
        self._checks: Dict[str, Callable[[], HealthCheckResult]] = {}
        self._last_results: Dict[str, HealthCheckResult] = {}

    def register(
        self,
        component: str,
        check_fn: Callable[[], HealthCheckResult],
    ) -> None:
        """Register health check for component.
        
        Args:
            component: Component name (unique identifier)
            check_fn: Async function returning HealthCheckResult
        
        Examples:
            >>> async def check_wallet():
            ...     return HealthCheckResult(
            ...         component="wallet",
            ...         status=HealthStatus.HEALTHY,
            ...     )
            >>> checker.register("wallet", check_wallet)
        """
        self._checks[component] = check_fn
        logger.info(f"Registered health check for component: {component}")

    def unregister(self, component: str) -> None:
        """Unregister health check.
        
        Args:
            component: Component name to unregister
        """
        if component in self._checks:
            del self._checks[component]
            logger.info(f"Unregistered health check for component: {component}")

    async def check_all(self) -> CompositeHealthStatus:
        """Execute all registered health checks.
        
        Returns:
            CompositeHealthStatus with aggregated results
        
        Examples:
            >>> status = await checker.check_all()
            >>> if not status.is_healthy:
            ...     print("System unhealthy!")
        """
        results: Dict[str, HealthCheckResult] = {}
        
        # Execute all checks concurrently
        check_tasks = [
            self._execute_check(component, check_fn)
            for component, check_fn in self._checks.items()
        ]
        
        check_results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Aggregate results
        for result in check_results:
            if isinstance(result, Exception):
                logger.error(f"Health check failed with exception", exc_info=result)
                continue
            
            results[result.component] = result
            self._last_results[result.component] = result
        
        # Determine overall status
        overall_status = self._aggregate_status(list(results.values()))
        
        return CompositeHealthStatus(
            overall_status=overall_status,
            components=results,
            timestamp=datetime.now(),
        )

    async def check_component(self, component: str) -> Optional[HealthCheckResult]:
        """Execute health check for specific component.
        
        Args:
            component: Component name to check
        
        Returns:
            HealthCheckResult or None if component not registered
        """
        check_fn = self._checks.get(component)
        if not check_fn:
            logger.warning(f"No health check registered for component: {component}")
            return None
        
        return await self._execute_check(component, check_fn)

    def get_last_result(self, component: str) -> Optional[HealthCheckResult]:
        """Get last health check result for component.
        
        Args:
            component: Component name
        
        Returns:
            Last HealthCheckResult or None
        """
        return self._last_results.get(component)

    async def _execute_check(
        self,
        component: str,
        check_fn: Callable[[], HealthCheckResult],
    ) -> HealthCheckResult:
        """Execute single health check with timing.
        
        Args:
            component: Component name
            check_fn: Health check function
        
        Returns:
            HealthCheckResult with latency measurement
        """
        start_time = datetime.now()
        
        try:
            result = await check_fn()
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Update latency if not set
            if result.latency_ms is None:
                result = HealthCheckResult(
                    component=result.component,
                    status=result.status,
                    message=result.message,
                    latency_ms=latency_ms,
                    timestamp=result.timestamp,
                )
            
            return result
        
        except Exception as e:
            logger.error(
                f"Health check failed for component {component}",
                exc_info=True,
            )
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message=f"Exception: {str(e)}",
            )

    def _aggregate_status(self, results: List[HealthCheckResult]) -> HealthStatus:
        """Aggregate component statuses into overall status.
        
        Logic:
        - HEALTHY if all components HEALTHY
        - DEGRADED if any component DEGRADED and none UNHEALTHY
        - UNHEALTHY if any component UNHEALTHY
        - UNKNOWN if no results
        
        Args:
            results: List of component health check results
        
        Returns:
            Aggregated HealthStatus
        """
        if not results:
            return HealthStatus.UNKNOWN
        
        statuses = {r.status for r in results}
        
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        
        if HealthStatus.UNKNOWN in statuses:
            return HealthStatus.UNKNOWN
        
        return HealthStatus.HEALTHY
