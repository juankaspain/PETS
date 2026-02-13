"""WebSocket client for real-time updates.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional

import websockets
from websockets.client import WebSocketClientProtocol

logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket client for real-time dashboard updates."""

    def __init__(self, base_url: str = "ws://localhost:8000") -> None:
        """Initialize WebSocket client.
        
        Args:
            base_url: Base WebSocket URL
        """
        self.base_url = base_url
        self.connections: Dict[str, Optional[WebSocketClientProtocol]] = {}
        self.handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {}
        self.running = False

    async def connect(self, topic: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Connect to WebSocket topic.
        
        Args:
            topic: Topic to subscribe (orderbook/{id}, positions/{id}, bots/status)
            handler: Callback function for messages
        """
        self.handlers[topic] = handler
        self.running = True
        
        uri = f"{self.base_url}/api/v1/ws/{topic}"
        
        while self.running:
            try:
                async with websockets.connect(uri) as websocket:
                    self.connections[topic] = websocket
                    logger.info(
                        "websocket_connected",
                        extra={"topic": topic},
                    )
                    
                    # Start heartbeat
                    asyncio.create_task(self._heartbeat(websocket))
                    
                    # Receive messages
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            handler(data)
                        except json.JSONDecodeError as e:
                            logger.error(
                                "websocket_parse_error",
                                extra={"topic": topic, "error": str(e)},
                            )
                        except Exception as e:
                            logger.error(
                                "websocket_handler_error",
                                extra={"topic": topic, "error": str(e)},
                            )
            except websockets.exceptions.WebSocketException as e:
                logger.warning(
                    "websocket_disconnected",
                    extra={"topic": topic, "error": str(e)},
                )
                self.connections[topic] = None
                
                if self.running:
                    # Exponential backoff reconnect
                    await asyncio.sleep(5)
            except Exception as e:
                logger.error(
                    "websocket_error",
                    extra={"topic": topic, "error": str(e)},
                )
                
                if self.running:
                    await asyncio.sleep(5)

    async def _heartbeat(self, websocket: WebSocketClientProtocol) -> None:
        """Send periodic heartbeat.
        
        Args:
            websocket: WebSocket connection
        """
        try:
            while self.running:
                await websocket.send("ping")
                await asyncio.sleep(30)
        except Exception as e:
            logger.warning(
                "heartbeat_failed",
                extra={"error": str(e)},
            )

    async def disconnect(self, topic: str) -> None:
        """Disconnect from topic.
        
        Args:
            topic: Topic to disconnect
        """
        if topic in self.connections and self.connections[topic]:
            await self.connections[topic].close()
            self.connections[topic] = None
        
        if topic in self.handlers:
            del self.handlers[topic]
        
        logger.info(
            "websocket_disconnected",
            extra={"topic": topic},
        )

    async def disconnect_all(self) -> None:
        """Disconnect all topics."""
        self.running = False
        
        for topic in list(self.connections.keys()):
            await self.disconnect(topic)
