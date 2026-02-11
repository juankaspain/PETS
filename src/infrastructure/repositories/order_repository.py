"""Order repository implementation with TimescaleDB + Redis.

Provides persistence and caching for trading orders.
"""

import json
import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from src.infrastructure.persistence.redis_client import RedisClient
from src.infrastructure.persistence.timescaledb import TimescaleDBClient

logger = logging.getLogger(__name__)


class OrderRepository:
    """Order repository with TimescaleDB persistence and Redis cache.

    Provides:
    - Order CRUD operations
    - Active order caching (TTL 30s)
    - Bot-specific order queries
    - Zone-based filtering
    - Status tracking

    Example:
        >>> repo = OrderRepository(db_client, redis_client)
        >>> order_id = await repo.create(
        ...     bot_id=1,
        ...     market_id="0x123...",
        ...     side="BUY",
        ...     size=Decimal("1000"),
        ...     price=Decimal("0.55"),
        ...     zone=2,
        ... )
        >>> order = await repo.get_by_id(order_id)
    """

    def __init__(
        self,
        db_client: TimescaleDBClient,
        redis_client: RedisClient,
        cache_ttl: int = 30,
    ) -> None:
        """Initialize order repository.

        Args:
            db_client: TimescaleDB client
            redis_client: Redis client
            cache_ttl: Cache TTL in seconds
        """
        self.db = db_client
        self.redis = redis_client
        self.cache_ttl = cache_ttl

    def _cache_key(self, order_id: UUID) -> str:
        """Generate cache key for order."""
        return f"order:{str(order_id)}"

    async def create(
        self,
        bot_id: int,
        market_id: str,
        side: str,
        size: Decimal,
        price: Decimal,
        zone: int,
        post_only: bool = True,
    ) -> UUID:
        """Create new order.

        Args:
            bot_id: Bot ID
            market_id: Market ID
            side: 'BUY' or 'SELL'
            size: Order size
            price: Limit price
            zone: Risk zone (1-5)
            post_only: Post-only flag

        Returns:
            Order ID
        """
        order_id = uuid4()

        query = """
            INSERT INTO orders (
                order_id, bot_id, market_id, side, size, price, zone,
                status, post_only, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, 'PENDING', $8, NOW(), NOW()
            )
        """

        await self.db.execute(
            query,
            order_id,
            bot_id,
            market_id,
            side.upper(),
            float(size),
            float(price),
            zone,
            post_only,
        )

        # Cache order
        order_data = {
            "order_id": str(order_id),
            "bot_id": bot_id,
            "market_id": market_id,
            "side": side.upper(),
            "size": float(size),
            "price": float(price),
            "zone": zone,
            "status": "PENDING",
            "post_only": post_only,
        }
        await self.redis.setex(
            self._cache_key(order_id),
            self.cache_ttl,
            json.dumps(order_data),
        )

        logger.info(
            "Order created",
            extra={
                "order_id": str(order_id),
                "bot_id": bot_id,
                "market_id": market_id,
                "side": side,
                "zone": zone,
            },
        )

        return order_id

    async def get_by_id(self, order_id: UUID) -> Optional[dict]:
        """Get order by ID.

        Checks cache first, falls back to database.

        Args:
            order_id: Order ID

        Returns:
            Order dict or None
        """
        # Check cache
        cached = await self.redis.get(self._cache_key(order_id))
        if cached:
            return json.loads(cached)

        # Query database
        query = "SELECT * FROM orders WHERE order_id = $1"
        row = await self.db.fetchrow(query, order_id)

        if row is None:
            return None

        order = dict(row)

        # Cache result
        await self.redis.setex(
            self._cache_key(order_id),
            self.cache_ttl,
            json.dumps(order, default=str),
        )

        return order

    async def update_status(
        self, order_id: UUID, status: str
    ) -> None:
        """Update order status.

        Args:
            order_id: Order ID
            status: New status
        """
        query = """
            UPDATE orders
            SET status = $2, updated_at = NOW()
            WHERE order_id = $1
        """

        await self.db.execute(query, order_id, status.upper())

        # Invalidate cache
        await self.redis.delete(self._cache_key(order_id))

        logger.info(
            "Order status updated",
            extra={"order_id": str(order_id), "status": status},
        )

    async def get_by_bot(
        self,
        bot_id: int,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get orders for bot.

        Args:
            bot_id: Bot ID
            status: Filter by status (None = all)
            limit: Max results

        Returns:
            List of order dicts
        """
        if status:
            query = """
                SELECT * FROM orders
                WHERE bot_id = $1 AND status = $2
                ORDER BY created_at DESC
                LIMIT $3
            """
            rows = await self.db.fetch(query, bot_id, status.upper(), limit)
        else:
            query = """
                SELECT * FROM orders
                WHERE bot_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """
            rows = await self.db.fetch(query, bot_id, limit)

        return [dict(row) for row in rows]

    async def cancel(self, order_id: UUID) -> None:
        """Cancel order.

        Args:
            order_id: Order ID
        """
        await self.update_status(order_id, "CANCELLED")
        logger.info("Order cancelled", extra={"order_id": str(order_id)})
