"""WebSocket client for real-time market data."""

import asyncio
import json
import logging
from typing import Callable

import websockets

logger = logging.getLogger(__name__)


class PolymarketWebSocketClient:
    """WebSocket client for Polymarket real-time data.
    
    Connects to Polymarket WebSocket API to receive real-time:
    - Market price updates
    - Orderbook changes
    - Trade executions
    
    Features:
    - Auto-reconnect on disconnect
    - Subscribe to specific markets
    - Callback-based event handling
    """

    def __init__(
        self,
        url: str = "wss://ws-subscriptions-clob.polymarket.com/ws/market",
    ):
        """Initialize WebSocket client.
        
        Args:
            url: WebSocket URL
        """
        self.url = url
        self.ws = None
        self.subscriptions = set()
        self.callbacks = {}
        self.running = False

    async def connect(self):
        """Connect to WebSocket."""
        logger.info("Connecting to Polymarket WebSocket", extra={"url": self.url})
        
        try:
            self.ws = await websockets.connect(self.url)
            self.running = True
            logger.info("WebSocket connected")
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise

    async def disconnect(self):
        """Disconnect from WebSocket."""
        logger.info("Disconnecting from WebSocket")
        self.running = False
        
        if self.ws:
            await self.ws.close()
            self.ws = None

    async def subscribe(
        self,
        market_id: str,
        callback: Callable[[dict], None],
    ):
        """Subscribe to market updates.
        
        Args:
            market_id: Market ID to subscribe
            callback: Callback function for updates
        """
        if market_id in self.subscriptions:
            logger.warning(f"Already subscribed to {market_id}")
            return
        
        # Subscribe message
        subscribe_msg = {
            "type": "subscribe",
            "market": market_id,
        }
        
        await self.ws.send(json.dumps(subscribe_msg))
        
        self.subscriptions.add(market_id)
        self.callbacks[market_id] = callback
        
        logger.info(f"Subscribed to market {market_id}")

    async def unsubscribe(self, market_id: str):
        """Unsubscribe from market updates.
        
        Args:
            market_id: Market ID to unsubscribe
        """
        if market_id not in self.subscriptions:
            logger.warning(f"Not subscribed to {market_id}")
            return
        
        # Unsubscribe message
        unsubscribe_msg = {
            "type": "unsubscribe",
            "market": market_id,
        }
        
        await self.ws.send(json.dumps(unsubscribe_msg))
        
        self.subscriptions.remove(market_id)
        del self.callbacks[market_id]
        
        logger.info(f"Unsubscribed from market {market_id}")

    async def listen(self):
        """Listen for WebSocket messages.
        
        Runs continuously and handles:
        - Price updates
        - Reconnection on disconnect
        - Callback execution
        """
        while self.running:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                
                # Handle message by type
                msg_type = data.get("type")
                
                if msg_type == "price_update":
                    market_id = data.get("market")
                    
                    if market_id in self.callbacks:
                        callback = self.callbacks[market_id]
                        callback(data)
                
                elif msg_type == "error":
                    logger.error(f"WebSocket error: {data.get('message')}")
                
            except websockets.ConnectionClosed:
                logger.warning("WebSocket connection closed, reconnecting...")
                await self.reconnect()
            
            except Exception as e:
                logger.error(f"WebSocket error: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def reconnect(self):
        """Reconnect to WebSocket with exponential backoff."""
        retry_delay = 1
        max_delay = 60
        
        while self.running:
            try:
                await self.connect()
                
                # Resubscribe to all markets
                for market_id in list(self.subscriptions):
                    callback = self.callbacks[market_id]
                    await self.subscribe(market_id, callback)
                
                logger.info("WebSocket reconnected and resubscribed")
                return
            
            except Exception as e:
                logger.error(f"Reconnection failed: {e}")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)

    async def start(self):
        """Start WebSocket client."""
        await self.connect()
        await self.listen()
