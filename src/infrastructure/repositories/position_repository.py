"""Position repository implementation with TimescaleDB + Redis.

Provides persistence and caching for trading positions.
"""

import json
import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from src.infrastructure.persistence.redis_client import RedisClient
from src.infrastructure.persistence.timescaledb import TimescaleDBClient

logger = logging.getLogger(__name__)


class PositionRepository:
    """Position repository with TimescaleDB persistence and Redis cache.

    Provides:
    - Position CRUD operations
    - Open position caching (TTL 30s)
    - P&L tracking (realized + unrealized)
    - Bot performance queries
    - Zone-based filtering

    Example:
        >>> repo = PositionRepository(db_client, redis_client)
        >>> pos_id = await repo.create(
        ...     bot_id=1,
        ...     order_id=order_id,
        ...     market_id="0x123...",
        ...     side="BUY",
        ...     size=Decimal("1000"),
        ...     entry_price=Decimal("0.55"),
        ...     zone=2,
        ... )
        >>> await repo.update_pnl(pos_id, unrealized=Decimal("50"))
    """

    def __init__(
        self,
        db_client: TimescaleDBClient,
        redis_client: RedisClient,
        cache_ttl: int = 30,
    ) -> None:
        """Initialize position repository.

        Args:
            db_client: TimescaleDB client
            redis_client: Redis client
            cache_ttl: Cache TTL in seconds
        """
        self.db = db_client
        self.redis = redis_client
        self.cache_ttl = cache_ttl

    def _cache_key(self, position_id: UUID) -> str:
        """Generate cache key for position."""
        return f"position:{str(position_id)}"

    async def create(
        self,
        bot_id: int,
        order_id: UUID,
        market_id: str,
        side: str,
        size: Decimal,
        entry_price: Decimal,
        zone: int,
    ) -> UUID:
        """Create new position.

        Args:
            bot_id: Bot ID
            order_id: Order ID that created position
            market_id: Market ID
            side: 'BUY' or 'SELL'
            size: Position size
            entry_price: Entry price
            zone: Risk zone (1-5)

        Returns:
            Position ID
        """
        position_id = uuid4()

        query = """
            INSERT INTO positions (
                position_id, bot_id, order_id, market_id, side,
                size, entry_price, zone, opened_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, NOW()
            )
        """

        await self.db.execute(
            query,
            position_id,
            bot_id,
            order_id,
            market_id,
            side.upper(),
            float(size),
            float(entry_price),
            zone,
        )

        # Cache position
        position_data = {
            "position_id": str(position_id),
            "bot_id": bot_id,
            "order_id": str(order_id),
            "market_id": market_id,
            "side": side.upper(),
            "size": float(size),
            "entry_price": float(entry_price),
            "zone": zone,
            "closed_at": None,
        }
        await self.redis.setex(
            self._cache_key(position_id),
            self.cache_ttl,
            json.dumps(position_data),
        )

        logger.info(
            "Position created",
            extra={
                "position_id": str(position_id),
                "bot_id": bot_id,
                "market_id": market_id,
                "side": side,
                "zone": zone,
            },
        )

        return position_id

    async def get_by_id(self, position_id: UUID) -> Optional[dict]:
        """Get position by ID.

        Checks cache first, falls back to database.

        Args:
            position_id: Position ID

        Returns:
            Position dict or None
        """
        # Check cache
        cached = await self.redis.get(self._cache_key(position_id))
        if cached:
            return json.loads(cached)

        # Query database
        query = "SELECT * FROM positions WHERE position_id = $1"
        row = await self.db.fetchrow(query, position_id)

        if row is None:
            return None

        position = dict(row)

        # Cache if still open
        if position["closed_at"] is None:
            await self.redis.setex(
                self._cache_key(position_id),
                self.cache_ttl,
                json.dumps(position, default=str),
            )

        return position

    async def update_pnl(
        self,
        position_id: UUID,
        current_price: Optional[Decimal] = None,
        realized: Optional[Decimal] = None,
        unrealized: Optional[Decimal] = None,
    ) -> None:
        """Update position P&L.

        Args:
            position_id: Position ID
            current_price: Current market price
            realized: Realized P&L
            unrealized: Unrealized P&L
        """
        updates = []
        params = [position_id]
        param_idx = 2

        if current_price is not None:
            updates.append(f"current_price = ${param_idx}")
            params.append(float(current_price))
            param_idx += 1

        if realized is not None:
            updates.append(f"realized_pnl = ${param_idx}")
            params.append(float(realized))
            param_idx += 1

        if unrealized is not None:
            updates.append(f"unrealized_pnl = ${param_idx}")
            params.append(float(unrealized))
            param_idx += 1

        if not updates:
            return

        query = f"""
            UPDATE positions
            SET {', '.join(updates)}
            WHERE position_id = $1
        """

        await self.db.execute(query, *params)

        # Invalidate cache
        await self.redis.delete(self._cache_key(position_id))

        logger.debug(
            "Position P&L updated",
            extra={"position_id": str(position_id)},
        )

    async def close(
        self,
        position_id: UUID,
        realized_pnl: Decimal,
    ) -> None:
        """Close position.

        Args:
            position_id: Position ID
            realized_pnl: Final realized P&L
        """
        query = """
            UPDATE positions
            SET closed_at = NOW(), realized_pnl = $2
            WHERE position_id = $1
        """

        await self.db.execute(query, position_id, float(realized_pnl))

        # Remove from cache
        await self.redis.delete(self._cache_key(position_id))

        logger.info(
            "Position closed",
            extra={
                "position_id": str(position_id),
                "realized_pnl": float(realized_pnl),
            },
        )

    async def get_open(
        self, bot_id: Optional[int] = None, limit: int = 100
    ) -> list[dict]:
        """Get open positions.

        Args:
            bot_id: Filter by bot (None = all bots)
            limit: Max results

        Returns:
            List of position dicts
        """
        if bot_id is not None:
            query = """
                SELECT * FROM positions
                WHERE bot_id = $1 AND closed_at IS NULL
                ORDER BY opened_at DESC
                LIMIT $2
            """
            rows = await self.db.fetch(query, bot_id, limit)
        else:
            query = """
                SELECT * FROM positions
                WHERE closed_at IS NULL
                ORDER BY opened_at DESC
                LIMIT $1
            """
            rows = await self.db.fetch(query, limit)

        return [dict(row) for row in rows]
