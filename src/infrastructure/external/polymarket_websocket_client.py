"""Polymarket WebSocket client for real-time data.

Provides persistent WebSocket connection with auto-reconnect,
heartbeat monitoring, and message queue.
"""

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Optional

import aiohttp

logger = logging.getLogger(__name__)


class PolymarketWebSocketClient:
    """Polymarket WebSocket client.

    Provides:
    - Persistent WebSocket connection
    - Auto-reconnect with exponential backoff
    - Heartbeat/ping-pong monitoring
    - Subscribe to: orderbook, trades, markets
    - Message queue with async iteration

    Example:
        >>> client = PolymarketWebSocketClient()
        >>> await client.connect()
        >>> await client.subscribe_orderbook(market_id)
        >>> async for message in client.messages():
        ...     if message['type'] == 'orderbook_update':
        ...         process_orderbook(message['data'])
        >>> await client.close()
    """

    def __init__(
        self,
        ws_url: str = "wss://ws.polymarket.com/v1",
        heartbeat_interval: int = 30,
        reconnect_delay: int = 5,
        max_reconnect_delay: int = 300,
    ) -> None:
        """Initialize WebSocket client.

        Args:
            ws_url: WebSocket URL
            heartbeat_interval: Seconds between heartbeats
            reconnect_delay: Initial reconnect delay
            max_reconnect_delay: Max reconnect delay
        """
        self.ws_url = ws_url
        self.heartbeat_interval = heartbeat_interval
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_delay = max_reconnect_delay

        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._message_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._running = False
        self._receive_task: Optional[asyncio.Task[None]] = None
        self._heartbeat_task: Optional[asyncio.Task[None]] = None
        self._subscriptions: set[str] = set()

    async def connect(self) -> None:
        """Connect to WebSocket."""
        if self._running:
            logger.warning("PolymarketWebSocketClient already connected")
            return

        logger.info("Connecting to Polymarket WebSocket", extra={"url": self.ws_url})
        self._running = True

        self._session = aiohttp.ClientSession()
        await self._connect_websocket()

        # Start tasks
        self._receive_task = asyncio.create_task(self._receive_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        logger.info("PolymarketWebSocketClient connected")

    async def close(self) -> None:
        """Close WebSocket connection."""
        if not self._running:
            return

        logger.info("Closing PolymarketWebSocketClient")
        self._running = False

        # Cancel tasks
        for task in [self._receive_task, self._heartbeat_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Close WebSocket
        if self._ws and not self._ws.closed:
            await self._ws.close()

        # Close session
        if self._session:
            await self._session.close()

        logger.info("PolymarketWebSocketClient closed")

    async def _connect_websocket(self) -> None:
        """Establish WebSocket connection."""
        if self._session is None:
            raise RuntimeError("Session not initialized")

        self._ws = await self._session.ws_connect(self.ws_url)
        logger.info("WebSocket connected")

        # Re-subscribe to previous subscriptions
        for subscription in self._subscriptions:
            await self._send_message({"action": "subscribe", "channel": subscription})

    async def _send_message(self, message: dict[str, Any]) -> None:
        """Send message to WebSocket.

        Args:
            message: Message dict to send
        """
        if self._ws is None or self._ws.closed:
            raise RuntimeError("WebSocket not connected")

        await self._ws.send_json(message)
        logger.debug("WebSocket message sent", extra={"message": message})

    async def _receive_loop(self) -> None:
        """Receive messages from WebSocket."""
        reconnect_delay = self.reconnect_delay

        while self._running:
            try:
                if self._ws is None or self._ws.closed:
                    logger.warning("WebSocket disconnected, reconnecting...")
                    await asyncio.sleep(reconnect_delay)
                    await self._connect_websocket()
                    reconnect_delay = self.reconnect_delay
                    continue

                msg = await self._ws.receive()

                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self._message_queue.put(data)

                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.warning("WebSocket closed by server")
                    break

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error("WebSocket error", extra={"error": msg.data})
                    break

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in receive loop", extra={"error": str(e)})
                reconnect_delay = min(reconnect_delay * 2, self.max_reconnect_delay)
                await asyncio.sleep(reconnect_delay)

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat."""
        while self._running:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                if self._ws and not self._ws.closed:
                    await self._ws.ping()
                    logger.debug("Heartbeat sent")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in heartbeat loop", extra={"error": str(e)})

    async def subscribe_orderbook(self, market_id: str) -> None:
        """Subscribe to orderbook updates.

        Args:
            market_id: Market ID
        """
        channel = f"orderbook:{market_id}"
        self._subscriptions.add(channel)
        await self._send_message({"action": "subscribe", "channel": channel})
        logger.info("Subscribed to orderbook", extra={"market_id": market_id})

    async def subscribe_trades(self, market_id: str) -> None:
        """Subscribe to trade updates.

        Args:
            market_id: Market ID
        """
        channel = f"trades:{market_id}"
        self._subscriptions.add(channel)
        await self._send_message({"action": "subscribe", "channel": channel})
        logger.info("Subscribed to trades", extra={"market_id": market_id})

    async def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from channel.

        Args:
            channel: Channel to unsubscribe
        """
        if channel in self._subscriptions:
            self._subscriptions.remove(channel)
            await self._send_message({"action": "unsubscribe", "channel": channel})
            logger.info("Unsubscribed from channel", extra={"channel": channel})

    async def messages(self) -> AsyncIterator[dict[str, Any]]:
        """Iterate over received messages.

        Yields:
            Message dicts

        Example:
            >>> async for msg in client.messages():
            ...     print(msg['type'], msg['data'])
        """
        while self._running:
            try:
                message = await asyncio.wait_for(
                    self._message_queue.get(), timeout=1.0
                )
                yield message
            except asyncio.TimeoutError:
                continue
