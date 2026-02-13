"""Tests for event bus.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import pytest

from src.application.orchestration.event_bus import Event, EventBus


@pytest.fixture
def event_bus():
    """Create event bus instance."""
    return EventBus()


@pytest.mark.asyncio
async def test_publish_subscribe(event_bus):
    """Test basic publish/subscribe."""
    received_events = []
    
    async def handler(event: Event):
        received_events.append(event)
    
    event_bus.subscribe("test.topic", handler)
    
    event = Event(
        topic="test.topic",
        payload={"key": "value"},
    )
    
    await event_bus.publish(event)
    
    assert len(received_events) == 1
    assert received_events[0].topic == "test.topic"
    assert received_events[0].payload["key"] == "value"


@pytest.mark.asyncio
async def test_wildcard_subscription(event_bus):
    """Test wildcard topic matching."""
    received_events = []
    
    async def handler(event: Event):
        received_events.append(event)
    
    event_bus.subscribe("position.*", handler)
    
    # Should match
    await event_bus.publish(
        Event(topic="position.opened", payload={})
    )
    await event_bus.publish(
        Event(topic="position.closed", payload={})
    )
    
    # Should not match
    await event_bus.publish(
        Event(topic="order.filled", payload={})
    )
    
    assert len(received_events) == 2
    assert all(e.topic.startswith("position.") for e in received_events)


@pytest.mark.asyncio
async def test_multiple_subscribers(event_bus):
    """Test multiple subscribers to same topic."""
    handler1_called = []
    handler2_called = []
    
    async def handler1(event: Event):
        handler1_called.append(True)
    
    async def handler2(event: Event):
        handler2_called.append(True)
    
    event_bus.subscribe("test", handler1)
    event_bus.subscribe("test", handler2)
    
    await event_bus.publish(Event(topic="test", payload={}))
    
    assert len(handler1_called) == 1
    assert len(handler2_called) == 1


@pytest.mark.asyncio
async def test_error_isolation(event_bus):
    """Test that handler errors don't affect other handlers."""
    handler2_called = []
    
    async def failing_handler(event: Event):
        raise ValueError("Handler error")
    
    async def working_handler(event: Event):
        handler2_called.append(True)
    
    event_bus.subscribe("test", failing_handler)
    event_bus.subscribe("test", working_handler)
    
    # Should not raise, working_handler should still be called
    await event_bus.publish(Event(topic="test", payload={}))
    
    assert len(handler2_called) == 1
