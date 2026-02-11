"""External service integrations.

Provides clients for:
- Polymarket CLOB (HTTP + WebSocket)
- Polygon RPC (Web3.py)
- Market data processing
"""

from src.infrastructure.external.market_data_processor import MarketDataProcessor
from src.infrastructure.external.polygon_rpc_client import PolygonRPCClient
from src.infrastructure.external.polymarket_clob_client import PolymarketCLOBClient
from src.infrastructure.external.polymarket_websocket_client import (
    PolymarketWebSocketClient,
)
from src.infrastructure.external.websocket_gateway import WebSocketGateway

__all__ = [
    "PolymarketCLOBClient",
    "PolymarketWebSocketClient",
    "PolygonRPCClient",
    "WebSocketGateway",
    "MarketDataProcessor",
]
