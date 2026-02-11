"""Market repository implementation with TimescaleDB + Redis.

Provides persistence and caching for market data.
"""

import json
import logging
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from src.infrastructure.persistence.redis_client import RedisClient
from src.infrastructure.persistence.timescaledb import TimescaleDBClient

logger = logging.getLogger(__name__)


class MarketRepository:
    """Market repository with TimescaleDB persistence and Redis cache.

    Provides:
    - Market CRUD operations
    - Market data caching (TTL 60s)
    - Price/liquidity tracking
    - Market snapshot history
    - Active market queries

    Example:
        >>> repo = MarketRepository(db_client, redis_client)
        >>> await repo.upsert(
        ...     market_id="0x123...",
        ...     question="Will X happen?",
        ...     outcomes=["YES", "NO"],
        ...     liquidity=Decimal("100000"),
        ... )
        >>> market = await repo.get_by_id("0x123...")
    """

    def __init__(
        self,
        db_client: TimescaleDBClient,
        redis_client: RedisClient,
        cache_ttl: int = 60,
    ) -> None:
        """Initialize market repository.

        Args:
            db_client: TimescaleDB client
            redis_client: Redis client
            cache_ttl: Cache TTL in seconds
        """
        self.db = db_client
        self.redis = redis_client
        self.cache_ttl = cache_ttl

    def _cache_key(self, market_id: str) -> str:
        """Generate cache key for market."""
        return f"market:{market_id}"

    async def upsert(
        self,
        market_id: str,
        question: str,
        outcomes: list[str],
        liquidity: Decimal,
        volume_24h: Optional[Decimal] = None,
        yes_price: Optional[Decimal] = None,
        no_price: Optional[Decimal] = None,
        resolves_at: Optional[str] = None,
    ) -> None:
        """Insert or update market.

        Args:
            market_id: Market ID
            question: Market question
            outcomes: List of outcomes
            liquidity: Current liquidity
            volume_24h: 24h volume
            yes_price: YES outcome price
            no_price: NO outcome price
            resolves_at: Resolution timestamp
        """
        query = """
            INSERT INTO markets (
                market_id, question, outcomes, liquidity, volume_24h,
                yes_price, no_price, resolves_at, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW()
            )
            ON CONFLICT (market_id)
            DO UPDATE SET
                liquidity = EXCLUDED.liquidity,
                volume_24h = EXCLUDED.volume_24h,
                yes_price = EXCLUDED.yes_price,
                no_price = EXCLUDED.no_price,
                updated_at = NOW()
        """

        await self.db.execute(
            query,
            market_id,
            question,
            json.dumps(outcomes),
            float(liquidity),
            float(volume_24h) if volume_24h else 0,
            float(yes_price) if yes_price else None,
            float(no_price) if no_price else None,
            resolves_at,
        )

        # Invalidate cache
        await self.redis.delete(self._cache_key(market_id))

        logger.debug("Market upserted", extra={"market_id": market_id})

    async def get_by_id(self, market_id: str) -> Optional[dict]:
        """Get market by ID.

        Checks cache first, falls back to database.

        Args:
            market_id: Market ID

        Returns:
            Market dict or None
        """
        # Check cache
        cached = await self.redis.get(self._cache_key(market_id))
        if cached:
            return json.loads(cached)

        # Query database
        query = "SELECT * FROM markets WHERE market_id = $1"
        row = await self.db.fetchrow(query, market_id)

        if row is None:
            return None

        market = dict(row)

        # Cache result
        await self.redis.setex(
            self._cache_key(market_id),
            self.cache_ttl,
            json.dumps(market, default=str),
        )

        return market

    async def get_active(self, limit: int = 100) -> list[dict]:
        """Get active markets.

        Args:
            limit: Max results

        Returns:
            List of market dicts
        """
        query = """
            SELECT * FROM markets
            WHERE resolved = FALSE
            AND (resolves_at IS NULL OR resolves_at > NOW())
            ORDER BY liquidity DESC
            LIMIT $1
        """

        rows = await self.db.fetch(query, limit)
        return [dict(row) for row in rows]

    async def update_prices(
        self,
        market_id: str,
        yes_price: Decimal,
        no_price: Decimal,
    ) -> None:
        """Update market prices.

        Args:
            market_id: Market ID
            yes_price: YES price
            no_price: NO price
        """
        query = """
            UPDATE markets
            SET yes_price = $2, no_price = $3, updated_at = NOW()
            WHERE market_id = $1
        """

        await self.db.execute(
            query, market_id, float(yes_price), float(no_price)
        )

        # Invalidate cache
        await self.redis.delete(self._cache_key(market_id))

        logger.debug(
            "Market prices updated",
            extra={"market_id": market_id, "yes": float(yes_price), "no": float(no_price)},
        )

    async def create_snapshot(
        self,
        market_id: str,
        yes_price: Decimal,
        no_price: Decimal,
        liquidity: Decimal,
        volume: Decimal,
    ) -> None:
        """Create market snapshot.

        Args:
            market_id: Market ID
            yes_price: YES price
            no_price: NO price
            liquidity: Liquidity
            volume: Volume
        """
        snapshot_id = uuid4()

        query = """
            INSERT INTO market_snapshots (
                snapshot_id, market_id, yes_price, no_price,
                liquidity, volume, snapshot_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, NOW()
            )
        """

        await self.db.execute(
            query,
            snapshot_id,
            market_id,
            float(yes_price),
            float(no_price),
            float(liquidity),
            float(volume),
        )

        logger.debug(
            "Market snapshot created",
            extra={"market_id": market_id, "snapshot_id": str(snapshot_id)},
        )
