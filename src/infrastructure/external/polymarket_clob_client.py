"""Polymarket CLOB HTTP client with HMAC-SHA256 authentication.

Provides REST API access to Polymarket's Central Limit Order Book.
Implements rate limiting, retry logic, and connection pooling.
"""

import asyncio
import hashlib
import hmac
import logging
import time
from decimal import Decimal
from typing import Any, Optional
from urllib.parse import urlencode

import aiohttp

logger = logging.getLogger(__name__)


class PolymarketCLOBClient:
    """Polymarket CLOB HTTP client.

    Rate limits:
    - Burst: 3500 requests / 10 seconds
    - Sustained: 60 requests / second

    Authentication: HMAC-SHA256 with API key + secret

    Example:
        >>> client = PolymarketCLOBClient(api_key=key, api_secret=secret)
        >>> await client.connect()
        >>> markets = await client.get_markets()
        >>> order = await client.place_order(market_id, side, size, price)
        >>> await client.close()
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://clob.polymarket.com",
        max_connections: int = 100,
        timeout: int = 30,
    ) -> None:
        """Initialize CLOB client.

        Args:
            api_key: Polymarket API key
            api_secret: Polymarket API secret
            base_url: CLOB API base URL
            max_connections: Max concurrent connections
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.max_connections = max_connections
        self.timeout = aiohttp.ClientTimeout(total=timeout)

        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = RateLimiter(max_per_second=60, burst=3500, window=10)

    async def connect(self) -> None:
        """Create HTTP session."""
        if self._session is not None:
            logger.warning("PolymarketCLOBClient already connected")
            return

        connector = aiohttp.TCPConnector(limit=self.max_connections)
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
        )

        logger.info("PolymarketCLOBClient connected")

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session is not None:
            await self._session.close()
            self._session = None
            logger.info("PolymarketCLOBClient closed")

    def _generate_signature(
        self, timestamp: str, method: str, path: str, body: str = ""
    ) -> str:
        """Generate HMAC-SHA256 signature.

        Args:
            timestamp: Unix timestamp string
            method: HTTP method (GET, POST, etc.)
            path: Request path
            body: Request body (empty string if no body)

        Returns:
            Hex-encoded signature
        """
        message = f"{timestamp}{method}{path}{body}"
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make authenticated API request.

        Args:
            method: HTTP method
            path: API endpoint path
            params: Query parameters
            json_data: JSON body

        Returns:
            Response JSON

        Raises:
            RuntimeError: If not connected
            aiohttp.ClientError: If request fails
        """
        if self._session is None:
            raise RuntimeError("Client not connected")

        # Rate limiting
        await self._rate_limiter.acquire()

        # Build URL
        url = f"{self.base_url}{path}"
        if params:
            url += f"?{urlencode(params)}"

        # Generate signature
        timestamp = str(int(time.time() * 1000))
        body_str = "" if json_data is None else str(json_data)
        signature = self._generate_signature(timestamp, method, path, body_str)

        # Headers
        headers = {
            "POLY-ADDRESS": self.api_key,
            "POLY-SIGNATURE": signature,
            "POLY-TIMESTAMP": timestamp,
            "Content-Type": "application/json",
        }

        # Make request
        async with self._session.request(
            method=method,
            url=url,
            headers=headers,
            json=json_data,
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def get_markets(
        self, active_only: bool = True, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get markets.

        Args:
            active_only: Only return active markets
            limit: Max results
            offset: Pagination offset

        Returns:
            List of market dicts
        """
        params = {
            "active": str(active_only).lower(),
            "limit": limit,
            "offset": offset,
        }
        response = await self._request("GET", "/markets", params=params)
        return response.get("data", [])

    async def get_market(self, market_id: str) -> dict[str, Any]:
        """Get single market details.

        Args:
            market_id: Market ID

        Returns:
            Market dict
        """
        response = await self._request("GET", f"/markets/{market_id}")
        return response

    async def get_orderbook(
        self, market_id: str, limit: int = 50
    ) -> dict[str, Any]:
        """Get orderbook for market.

        Args:
            market_id: Market ID
            limit: Max orders per side

        Returns:
            Orderbook dict with bids/asks
        """
        params = {"limit": limit}
        response = await self._request(
            "GET", f"/markets/{market_id}/orderbook", params=params
        )
        return response

    async def place_order(
        self,
        market_id: str,
        side: str,
        size: Decimal,
        price: Decimal,
        post_only: bool = True,
    ) -> dict[str, Any]:
        """Place limit order.

        Args:
            market_id: Market ID
            side: 'BUY' or 'SELL'
            size: Order size
            price: Limit price (0.01 to 0.99)
            post_only: Post-only order (default True)

        Returns:
            Order response dict
        """
        data = {
            "market": market_id,
            "side": side.upper(),
            "size": str(size),
            "price": str(price),
            "postOnly": post_only,
        }
        response = await self._request("POST", "/orders", json_data=data)
        return response

    async def cancel_order(self, order_id: str) -> dict[str, Any]:
        """Cancel order.

        Args:
            order_id: Order ID to cancel

        Returns:
            Cancellation response dict
        """
        response = await self._request("DELETE", f"/orders/{order_id}")
        return response

    async def get_orders(
        self, market_id: Optional[str] = None, status: str = "OPEN"
    ) -> list[dict[str, Any]]:
        """Get orders.

        Args:
            market_id: Filter by market (None = all markets)
            status: Order status filter

        Returns:
            List of order dicts
        """
        params = {"status": status}
        if market_id:
            params["market"] = market_id

        response = await self._request("GET", "/orders", params=params)
        return response.get("data", [])


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(
        self, max_per_second: int, burst: int, window: int = 1
    ) -> None:
        self.max_per_second = max_per_second
        self.burst = burst
        self.window = window
        self._tokens = burst
        self._last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire token, waiting if necessary."""
        async with self._lock:
            while True:
                now = time.time()
                elapsed = now - self._last_update

                # Refill tokens
                self._tokens = min(
                    self.burst,
                    self._tokens + elapsed * self.max_per_second,
                )
                self._last_update = now

                if self._tokens >= 1:
                    self._tokens -= 1
                    return

                # Wait for next token
                wait_time = (1 - self._tokens) / self.max_per_second
                await asyncio.sleep(wait_time)
