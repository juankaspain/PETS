"""Event bus for decoupled component communication.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Event:
    """Base event class."""

    topic: str
    payload: Dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    correlation_id: Optional[str] = None


class EventBus:
    """Async event bus for pub/sub communication.
    
    Supports:
    - Topic-based routing (e.g., "position.opened", "order.filled")
    - Multiple subscribers per topic
    - Wildcard subscriptions (e.g., "position.*")
    - Error isolation between subscribers
    
    Examples:
        >>> bus = EventBus()
        >>> 
        >>> async def handle_position_opened(event: Event):
        ...     print(f"Position opened: {event.payload}")
        >>> 
        >>> bus.subscribe("position.opened", handle_position_opened)
        >>> await bus.publish(
        ...     Event(
        ...         topic="position.opened",
        ...         payload={"position_id": 123},
        ...     )
        ... )
    """

    def __init__(self) -> None:
        """Initialize event bus."""
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._lock = asyncio.Lock()

    def subscribe(
        self,
        topic: str,
        handler: Callable[[Event], None],
    ) -> None:
        """Subscribe to topic.
        
        Args:
            topic: Topic to subscribe to (supports wildcards: "position.*")
            handler: Async function to handle events
        
        Examples:
            >>> async def on_order_filled(event: Event):
            ...     print(f"Order {event.payload['order_id']} filled")
            >>> 
            >>> bus.subscribe("order.filled", on_order_filled)
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        
        self._subscribers[topic].append(handler)
        logger.info(f"Subscriber registered for topic: {topic}")

    def unsubscribe(
        self,
        topic: str,
        handler: Callable[[Event], None],
    ) -> None:
        """Unsubscribe from topic.
        
        Args:
            topic: Topic to unsubscribe from
            handler: Handler function to remove
        """
        if topic in self._subscribers:
            try:
                self._subscribers[topic].remove(handler)
                logger.info(f"Subscriber removed for topic: {topic}")
            except ValueError:
                logger.warning(
                    f"Handler not found for topic: {topic}"
                )

    async def publish(self, event: Event) -> None:
        """Publish event to all matching subscribers.
        
        Args:
            event: Event to publish
        
        Examples:
            >>> await bus.publish(
            ...     Event(
            ...         topic="risk.alert",
            ...         payload={"bot_id": 8, "message": "Drawdown exceeded"},
            ...     )
            ... )
        """
        logger.debug(f"Publishing event: {event.topic} [{event.event_id}]")
        
        # Find matching subscribers
        handlers = self._get_matching_handlers(event.topic)
        
        if not handlers:
            logger.debug(f"No subscribers for topic: {event.topic}")
            return
        
        # Invoke all handlers concurrently
        tasks = [
            self._invoke_handler(handler, event)
            for handler in handlers
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)

    def _get_matching_handlers(
        self,
        topic: str,
    ) -> List[Callable[[Event], None]]:
        """Get handlers matching topic (including wildcards).
        
        Args:
            topic: Topic to match
        
        Returns:
            List of matching handlers
        
        Examples:
            >>> # For topic "position.opened"
            >>> # Matches: "position.opened", "position.*", "*"
        """
        handlers: List[Callable[[Event], None]] = []
        
        for pattern, pattern_handlers in self._subscribers.items():
            if self._topic_matches(topic, pattern):
                handlers.extend(pattern_handlers)
        
        return handlers

    def _topic_matches(self, topic: str, pattern: str) -> bool:
        """Check if topic matches pattern.
        
        Args:
            topic: Actual topic (e.g., "position.opened")
            pattern: Pattern with wildcards (e.g., "position.*")
        
        Returns:
            True if topic matches pattern
        """
        # Exact match
        if topic == pattern:
            return True
        
        # Wildcard match
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return topic.startswith(prefix + ".")
        
        # Full wildcard
        if pattern == "*":
            return True
        
        return False

    async def _invoke_handler(
        self,
        handler: Callable[[Event], None],
        event: Event,
    ) -> None:
        """Invoke event handler with error isolation.
        
        Args:
            handler: Handler function
            event: Event to pass to handler
        """
        try:
            await handler(event)
        except Exception as e:
            logger.error(
                f"Error in event handler for topic {event.topic}",
                exc_info=True,
            )
