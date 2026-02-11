"""WebSocket gateway for managing multiple connections.

Provides centralized WebSocket management with message routing.
"""

import asyncio
import logging
from typing import Any, Callable, Awaitable, Optional

from src.infrastructure.external.polymarket_websocket_client import (
    PolymarketWebSocketClient,
)

logger = logging.getLogger(__name__)

MessageHandler = Callable[[str, dict[str, Any]], Awaitable[None]]


class WebSocketGateway:
    """Manages multiple WebSocket connections.

    Provides:
    - Connection pool management
    - Message routing by channel
    - Connection health monitoring
    - Graceful shutdown

    Example:
        >>> gateway = WebSocketGateway()
        >>> await gateway.start()
        >>>
        >>> async def handle_orderbook(channel: str, data: dict) -> None:
        ...     print(f"Orderbook update: {channel}")
        >>>
        >>> await gateway.subscribe("orderbook:market123", handle_orderbook)
        >>> await gateway.stop()
    """

    def __init__(self) -> None:
        """Initialize WebSocket gateway."""
        self._client: Optional[PolymarketWebSocketClient] = None
        self._handlers: dict[str, list[MessageHandler]] = {}
        self._router_task: Optional[asyncio.Task[None]] = None
        self._running = False

    async def start(self) -> None:
        """Start WebSocket gateway."""
        if self._running:
            logger.warning("WebSocketGateway already running")
            return

        logger.info("Starting WebSocketGateway")
        self._running = True

        # Create WebSocket client
        self._client = PolymarketWebSocketClient()
        await self._client.connect()

        # Start message router
        self._router_task = asyncio.create_task(self._route_messages())

        logger.info("WebSocketGateway started")

    async def stop(self) -> None:
        """Stop WebSocket gateway."""
        if not self._running:
            return

        logger.info("Stopping WebSocketGateway")
        self._running = False

        # Cancel router
        if self._router_task and not self._router_task.done():
            self._router_task.cancel()
            try:
                await self._router_task
            except asyncio.CancelledError:
                pass

        # Close client
        if self._client:
            await self._client.close()

        self._handlers.clear()
        logger.info("WebSocketGateway stopped")

    async def subscribe(
        self,
        channel: str,
        handler: MessageHandler,
    ) -> None:
        """Subscribe to channel with handler.

        Args:
            channel: Channel name (e.g., 'orderbook:market123')
            handler: Async message handler

        Example:
            >>> async def handle_msg(channel: str, data: dict) -> None:
            ...     print(f"{channel}: {data}")
            >>>
            >>> await gateway.subscribe("orderbook:market123", handle_msg)
        """
        if not self._running or self._client is None:
            raise RuntimeError("Gateway not started")

        # Add handler
        if channel not in self._handlers:
            self._handlers[channel] = []
            # Subscribe via client
            if channel.startswith("orderbook:"):
                market_id = channel.split(":", 1)[1]
                await self._client.subscribe_orderbook(market_id)
            elif channel.startswith("trades:"):
                market_id = channel.split(":", 1)[1]
                await self._client.subscribe_trades(market_id)

        self._handlers[channel].append(handler)

        logger.info(
            "Subscribed to channel",
            extra={"channel": channel, "handler_count": len(self._handlers[channel])},
        )

    async def unsubscribe(
        self,
        channel: str,
        handler: Optional[MessageHandler] = None,
    ) -> None:
        """Unsubscribe from channel.

        Args:
            channel: Channel name
            handler: Specific handler (None = remove all)
        """
        if channel not in self._handlers:
            return

        if handler is None:
            # Remove all handlers
            del self._handlers[channel]
            if self._client:
                await self._client.unsubscribe(channel)
            logger.info("Unsubscribed from channel", extra={"channel": channel})
        else:
            # Remove specific handler
            if handler in self._handlers[channel]:
                self._handlers[channel].remove(handler)
                if not self._handlers[channel]:
                    del self._handlers[channel]
                    if self._client:
                        await self._client.unsubscribe(channel)

    async def _route_messages(self) -> None:
        """Route messages to handlers."""
        if self._client is None:
            return

        try:
            async for message in self._client.messages():
                # Extract channel from message
                channel = message.get("channel")
                if not channel:
                    logger.warning("Message without channel", extra={"message": message})
                    continue

                # Route to handlers
                if channel in self._handlers:
                    for handler in self._handlers[channel]:
                        try:
                            await handler(channel, message)
                        except Exception as e:
                            logger.error(
                                "Handler error",
                                extra={"channel": channel, "error": str(e)},
                            )

        except asyncio.CancelledError:
            logger.info("Message router cancelled")
        except Exception as e:
            logger.error("Error in message router", extra={"error": str(e)})
