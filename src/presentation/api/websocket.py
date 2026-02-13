"""WebSocket endpoints for real-time updates.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import asyncio
import json
import logging
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self) -> None:
        # topic -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, topic: str) -> None:
        """Accept WebSocket connection."""
        await websocket.accept()
        
        async with self.lock:
            if topic not in self.active_connections:
                self.active_connections[topic] = set()
            self.active_connections[topic].add(websocket)
        
        logger.info(
            "websocket_connected",
            extra={
                "topic": topic,
                "total_connections": len(self.active_connections.get(topic, set())),
            },
        )

    async def disconnect(self, websocket: WebSocket, topic: str) -> None:
        """Remove WebSocket connection."""
        async with self.lock:
            if topic in self.active_connections:
                self.active_connections[topic].discard(websocket)
                if not self.active_connections[topic]:
                    del self.active_connections[topic]
        
        logger.info(
            "websocket_disconnected",
            extra={
                "topic": topic,
                "remaining_connections": len(self.active_connections.get(topic, set())),
            },
        )

    async def broadcast(self, topic: str, message: dict) -> None:
        """Broadcast message to all connections on topic."""
        if topic not in self.active_connections:
            return
        
        message_json = json.dumps(message)
        dead_connections = set()
        
        for connection in self.active_connections[topic]:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(
                    "websocket_send_failed",
                    extra={"topic": topic, "error": str(e)},
                )
                dead_connections.add(connection)
        
        # Clean up dead connections
        if dead_connections:
            async with self.lock:
                self.active_connections[topic] -= dead_connections


manager = ConnectionManager()


@router.websocket("/orderbook/{market_id}")
async def websocket_orderbook(websocket: WebSocket, market_id: str) -> None:
    """Real-time orderbook updates for market.
    
    Args:
        websocket: WebSocket connection
        market_id: Market identifier
    """
    topic = f"orderbook:{market_id}"
    await manager.connect(websocket, topic)
    
    try:
        # Send initial snapshot
        await websocket.send_json({
            "type": "snapshot",
            "market_id": market_id,
            "bids": [],
            "asks": [],
        })
        
        # Keep connection alive
        while True:
            # Receive heartbeat/ping from client
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(websocket, topic)
    except Exception as e:
        logger.error(
            "websocket_error",
            extra={"topic": topic, "error": str(e)},
        )
        await manager.disconnect(websocket, topic)


@router.websocket("/positions/{bot_id}")
async def websocket_positions(websocket: WebSocket, bot_id: int) -> None:
    """Real-time position updates for bot.
    
    Args:
        websocket: WebSocket connection
        bot_id: Bot identifier
    """
    topic = f"positions:{bot_id}"
    await manager.connect(websocket, topic)
    
    try:
        # Send initial positions
        await websocket.send_json({
            "type": "snapshot",
            "bot_id": bot_id,
            "positions": [],
        })
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(websocket, topic)
    except Exception as e:
        logger.error(
            "websocket_error",
            extra={"topic": topic, "error": str(e)},
        )
        await manager.disconnect(websocket, topic)


@router.websocket("/bots/status")
async def websocket_bot_status(websocket: WebSocket) -> None:
    """Real-time bot status updates.
    
    Args:
        websocket: WebSocket connection
    """
    topic = "bots:status"
    await manager.connect(websocket, topic)
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "snapshot",
            "bots": [],
        })
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(websocket, topic)
    except Exception as e:
        logger.error(
            "websocket_error",
            extra={"topic": topic, "error": str(e)},
        )
        await manager.disconnect(websocket, topic)
