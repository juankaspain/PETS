"""Redis Pub/Sub event bus implementation.

Provides at-least-once delivery of domain events using Redis pub/sub.
Supports multiple consumers per channel and event serialization.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Awaitable, Optional
from uuid import uuid4

from src.infrastructure.persistence.redis_client import RedisClient

logger = logging.getLogger(__name__)

EventHandler = Callable[[dict[str, Any]], Awaitable[None]]


class RedisPubSubEventBus:
    """Redis-based event bus with pub/sub pattern.

    Provides:
    - At-least-once delivery guarantee
    - Multiple consumers per channel
    - Event serialization/deserialization
    - Correlation ID tracking
    - Subscribe/unsubscribe pattern

    Example:
        >>> bus = RedisPubSubEventBus(redis_client)
        >>> await bus.start()
        >>>
        >>> async def handle_order(event: dict) -> None:
        ...     print(f"Order placed: {event['order_id']}")
        >>>
        >>> await bus.subscribe("events.orders", handle_order)
        >>> await bus.publish("events.orders", {"order_id": "123"})
        >>> await bus.stop()
    """

    def __init__(self, redis_client: RedisClient) -> None:
        """Initialize event bus.

        Args:
            redis_client: Connected Redis client
        """
        self.redis = redis_client
        self._handlers: dict[str, list[EventHandler]] = {}
        self._pubsub: Optional[Any] = None
        self._listener_task: Optional[asyncio.Task[None]] = None
        self._running = False

    async def start(self) -> None:
        """Start event bus listener.

        Raises:
            RuntimeError: If Redis client not connected
        """
        if not self.redis.is_connected:
            raise RuntimeError("Redis client not connected")

        if self._running:
            logger.warning("Event bus already running")
            return

        logger.info("Starting event bus")
        self._running = True
        self._pubsub = await self.redis.subscribe()  # Subscribe to channels later

        logger.info("Event bus started")

    async def stop(self) -> None:
        """Stop event bus gracefully."""
        if not self._running:
            return

        logger.info("Stopping event bus")
        self._running = False

        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()

        self._handlers.clear()
        logger.info("Event bus stopped")

    async def publish(
        self,
        channel: str,
        event: dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> None:
        """Publish event to channel.

        Args:
            channel: Channel name (e.g., "events.orders")
            event: Event data dictionary
            correlation_id: Optional correlation ID for tracing

        Raises:
            RuntimeError: If event bus not started

        Example:
            >>> await bus.publish(
            ...     "events.orders",
            ...     {"order_id": "123", "bot_id": 8, "status": "FILLED"},
            ...     correlation_id="req-abc-123",
            ... )
        """
        if not self._running:
            raise RuntimeError("Event bus not started")

        # Add metadata
        message = {
            "event": event,
            "correlation_id": correlation_id or str(uuid4()),
            "channel": channel,
        }

        logger.debug(
            "Publishing event",
            extra={
                "channel": channel,
                "correlation_id": message["correlation_id"],
            },
        )

        await self.redis.publish(channel, message)

    async def subscribe(
        self,
        channel: str,
        handler: EventHandler,
    ) -> None:
        """Subscribe to channel with handler.

        Args:
            channel: Channel name (e.g., "events.orders")
            handler: Async function to handle events

        Raises:
            RuntimeError: If event bus not started

        Example:
            >>> async def handle_order(event: dict) -> None:
            ...     order_id = event["order_id"]
            ...     logger.info(f"Processing order {order_id}")
            >>>
            >>> await bus.subscribe("events.orders", handle_order)
        """
        if not self._running:
            raise RuntimeError("Event bus not started")

        if channel not in self._handlers:
            self._handlers[channel] = []
            # Subscribe to Redis channel
            if self._pubsub:
                await self._pubsub.subscribe(channel)
                # Start listener if not running
                if self._listener_task is None or self._listener_task.done():
                    self._listener_task = asyncio.create_task(self._listen())

        self._handlers[channel].append(handler)

        logger.info(
            "Subscribed to channel",
            extra={
                "channel": channel,
                "handler_count": len(self._handlers[channel]),
            },
        )

    async def unsubscribe(
        self,
        channel: str,
        handler: Optional[EventHandler] = None,
    ) -> None:
        """Unsubscribe from channel.

        Args:
            channel: Channel name
            handler: Specific handler to remove (None = remove all)

        Example:
            >>> await bus.unsubscribe("events.orders")  # Remove all handlers
            >>> await bus.unsubscribe("events.orders", handle_order)  # Remove specific
        """
        if channel not in self._handlers:
            return

        if handler is None:
            # Remove all handlers for channel
            del self._handlers[channel]
            if self._pubsub:
                await self._pubsub.unsubscribe(channel)
            logger.info("Unsubscribed from channel", extra={"channel": channel})
        else:
            # Remove specific handler
            if handler in self._handlers[channel]:
                self._handlers[channel].remove(handler)
                if not self._handlers[channel]:
                    # No more handlers, unsubscribe from Redis
                    del self._handlers[channel]
                    if self._pubsub:
                        await self._pubsub.unsubscribe(channel)
                logger.info(
                    "Removed handler from channel",
                    extra={"channel": channel},
                )

    async def _listen(self) -> None:
        """Listen for messages on subscribed channels."""
        if not self._pubsub:
            return

        logger.info("Event bus listener started")

        try:
            async for message in self._pubsub.listen():
                if not self._running:
                    break

                if message["type"] != "message":
                    continue

                channel = message["channel"]
                if isinstance(channel, bytes):
                    channel = channel.decode("utf-8")

                if channel not in self._handlers:
                    continue

                # Deserialize message
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        logger.error(
                            "Failed to deserialize message",
                            extra={"channel": channel, "data": data},
                        )
                        continue

                # Extract event
                event = data.get("event", data)
                correlation_id = data.get("correlation_id")

                # Call all handlers
                for handler in self._handlers[channel]:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(
                            "Event handler failed",
                            extra={
                                "channel": channel,
                                "correlation_id": correlation_id,
                                "error": str(e),
                            },
                        )

        except asyncio.CancelledError:
            logger.info("Event bus listener cancelled")
        except Exception as e:
            logger.error("Event bus listener error", extra={"error": str(e)})
        finally:
            logger.info("Event bus listener stopped")
