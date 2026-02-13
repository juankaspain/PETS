"""Integration tests for orchestration.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.orchestration.bot_orchestrator import OrchestratorConfig
from src.application.orchestration.event_bus import Event, EventBus
from src.application.orchestration.factory import OrchestratorFactory
from src.application.orchestration.health_checker import (
    HealthCheckResult,
    HealthChecker,
    HealthStatus,
)
from src.domain.entities.bot import Bot, BotState, StrategyType


@pytest.fixture
def event_bus():
    """Create event bus."""
    return EventBus()


@pytest.fixture
def health_checker():
    """Create health checker."""
    return HealthChecker()


@pytest.fixture
def factory(event_bus, health_checker):
    """Create orchestrator factory."""
    factory = OrchestratorFactory()
    
    # Register singletons
    factory.register_singleton(EventBus, event_bus)
    factory.register_singleton(HealthChecker, health_checker)
    
    # Register mocked services
    factory.register("BotRepository", AsyncMock())
    factory.register("PositionService", AsyncMock())
    factory.register("RiskService", AsyncMock())
    
    return factory


@pytest.mark.asyncio
async def test_end_to_end_bot_lifecycle(factory, event_bus):
    """Test complete bot lifecycle with events."""
    # Track events
    events_received = []
    
    async def event_handler(event: Event):
        events_received.append(event.topic)
    
    event_bus.subscribe("bot.*", event_handler)
    
    # Create bot
    bot = Bot(
        bot_id=8,
        strategy_type=StrategyType.TAIL_RISK,
        capital_allocated=5000.0,
        state=BotState.IDLE,
        created_at=datetime.now(),
    )
    
    # Create orchestrator
    orchestrator = factory.create_orchestrator(
        bot,
        config=OrchestratorConfig(
            health_check_interval_seconds=1,
        ),
    )
    
    # Start
    await orchestrator.start()
    await event_bus.publish(
        Event(topic="bot.started", payload={"bot_id": bot.bot_id})
    )
    
    assert orchestrator.state.value == "RUNNING"
    
    # Pause
    await orchestrator.pause()
    await event_bus.publish(
        Event(topic="bot.paused", payload={"bot_id": bot.bot_id})
    )
    
    assert orchestrator.state.value == "PAUSED"
    
    # Resume
    await orchestrator.resume()
    await event_bus.publish(
        Event(topic="bot.resumed", payload={"bot_id": bot.bot_id})
    )
    
    assert orchestrator.state.value == "RUNNING"
    
    # Stop
    await orchestrator.stop()
    await event_bus.publish(
        Event(topic="bot.stopped", payload={"bot_id": bot.bot_id})
    )
    
    assert orchestrator.state.value == "STOPPED"
    
    # Verify events
    assert "bot.started" in events_received
    assert "bot.paused" in events_received
    assert "bot.resumed" in events_received
    assert "bot.stopped" in events_received


@pytest.mark.asyncio
async def test_health_monitoring_integration(factory, health_checker):
    """Test health monitoring integration."""
    # Register health checks
    async def check_wallet():
        return HealthCheckResult(
            component="wallet",
            status=HealthStatus.HEALTHY,
        )
    
    async def check_database():
        return HealthCheckResult(
            component="database",
            status=HealthStatus.HEALTHY,
        )
    
    health_checker.register("wallet", check_wallet)
    health_checker.register("database", check_database)
    
    # Check health
    status = await health_checker.check_all()
    
    assert status.is_healthy
    assert len(status.components) == 2
    assert "wallet" in status.components
    assert "database" in status.components


@pytest.mark.asyncio
async def test_multi_bot_orchestration(factory):
    """Test orchestrating multiple bots."""
    # Create multiple bots
    bot1 = Bot(
        bot_id=1,
        strategy_type=StrategyType.TAIL_RISK,
        capital_allocated=5000.0,
        state=BotState.IDLE,
        created_at=datetime.now(),
    )
    
    bot2 = Bot(
        bot_id=2,
        strategy_type=StrategyType.TAIL_RISK,
        capital_allocated=3000.0,
        state=BotState.IDLE,
        created_at=datetime.now(),
    )
    
    # Create orchestrators
    orch1 = factory.create_orchestrator(bot1)
    orch2 = factory.create_orchestrator(bot2)
    
    # Start all
    await factory.start_all()
    
    assert orch1.state.value == "RUNNING"
    assert orch2.state.value == "RUNNING"
    
    # Stop all
    await factory.stop_all()
    
    assert orch1.state.value == "STOPPED"
    assert orch2.state.value == "STOPPED"


@pytest.mark.asyncio
async def test_event_bus_pub_sub_integration(event_bus):
    """Test event bus publish/subscribe integration."""
    position_events = []
    order_events = []
    
    async def position_handler(event: Event):
        position_events.append(event)
    
    async def order_handler(event: Event):
        order_events.append(event)
    
    # Subscribe
    event_bus.subscribe("position.*", position_handler)
    event_bus.subscribe("order.*", order_handler)
    
    # Publish events
    await event_bus.publish(
        Event(
            topic="position.opened",
            payload={"position_id": 123, "bot_id": 8},
        )
    )
    
    await event_bus.publish(
        Event(
            topic="order.filled",
            payload={"order_id": "abc123", "bot_id": 8},
        )
    )
    
    await event_bus.publish(
        Event(
            topic="position.closed",
            payload={"position_id": 123},
        )
    )
    
    # Verify
    assert len(position_events) == 2
    assert len(order_events) == 1
    
    assert position_events[0].topic == "position.opened"
    assert position_events[1].topic == "position.closed"
    assert order_events[0].topic == "order.filled"
