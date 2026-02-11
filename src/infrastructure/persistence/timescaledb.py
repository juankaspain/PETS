"""TimescaleDB client with AsyncPG connection pool.

Provides async PostgreSQL operations with TimescaleDB hypertables support.
Uses connection pooling for performance and proper resource management.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

import asyncpg
from asyncpg import Pool, Connection, Record

logger = logging.getLogger(__name__)


class TimescaleDBClient:
    """AsyncPG client for TimescaleDB operations.

    Provides connection pooling, health checks, and query helpers.
    Supports TimescaleDB hypertables, continuous aggregates, and compression.

    Example:
        >>> client = TimescaleDBClient(dsn="postgresql://...")
        >>> await client.connect()
        >>> result = await client.fetch("SELECT * FROM orders WHERE bot_id = $1", bot_id)
        >>> await client.close()
    """

    def __init__(
        self,
        dsn: str,
        min_size: int = 20,
        max_size: int = 50,
        command_timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        """Initialize TimescaleDB client.

        Args:
            dsn: PostgreSQL connection string
            min_size: Minimum connection pool size
            max_size: Maximum connection pool size
            command_timeout: Default query timeout in seconds
            **kwargs: Additional asyncpg pool parameters
        """
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.command_timeout = command_timeout
        self.kwargs = kwargs
        self._pool: Optional[Pool] = None
        self._connected = False

    async def connect(self) -> None:
        """Create connection pool.

        Raises:
            asyncpg.PostgresError: If connection fails
        """
        if self._connected:
            logger.warning("TimescaleDB already connected")
            return

        logger.info(
            "Connecting to TimescaleDB",
            extra={"min_size": self.min_size, "max_size": self.max_size},
        )

        self._pool = await asyncpg.create_pool(
            dsn=self.dsn,
            min_size=self.min_size,
            max_size=self.max_size,
            command_timeout=self.command_timeout,
            **self.kwargs,
        )
        self._connected = True

        logger.info("TimescaleDB connected successfully")

    async def close(self) -> None:
        """Close connection pool gracefully."""
        if not self._connected or self._pool is None:
            return

        logger.info("Closing TimescaleDB connection pool")
        await self._pool.close()
        self._connected = False
        logger.info("TimescaleDB connection pool closed")

    async def health_check(self) -> bool:
        """Check database health.

        Returns:
            True if database is healthy, False otherwise
        """
        if not self._connected or self._pool is None:
            return False

        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error("TimescaleDB health check failed", extra={"error": str(e)})
            return False

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[Connection]:
        """Acquire connection from pool.

        Yields:
            Database connection

        Raises:
            RuntimeError: If client not connected

        Example:
            >>> async with client.acquire() as conn:
            ...     result = await conn.fetch("SELECT * FROM orders")
        """
        if not self._connected or self._pool is None:
            raise RuntimeError("TimescaleDB client not connected")

        async with self._pool.acquire() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[Connection]:
        """Acquire connection and start transaction.

        Yields:
            Database connection with active transaction

        Raises:
            RuntimeError: If client not connected

        Example:
            >>> async with client.transaction() as conn:
            ...     await conn.execute("INSERT INTO orders ...")
            ...     await conn.execute("UPDATE positions ...")
        """
        if not self._connected or self._pool is None:
            raise RuntimeError("TimescaleDB client not connected")

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                yield conn

    async def fetch(
        self,
        query: str,
        *args: Any,
        timeout: Optional[float] = None,
    ) -> list[Record]:
        """Execute query and fetch all results.

        Args:
            query: SQL query with $1, $2 placeholders
            *args: Query parameters
            timeout: Query timeout (overrides default)

        Returns:
            List of result records

        Raises:
            RuntimeError: If client not connected
            asyncpg.PostgresError: If query fails
        """
        if not self._connected or self._pool is None:
            raise RuntimeError("TimescaleDB client not connected")

        logger.debug(
            "Executing fetch query",
            extra={"query": query, "args": args, "timeout": timeout},
        )

        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args, timeout=timeout)

    async def fetchrow(
        self,
        query: str,
        *args: Any,
        timeout: Optional[float] = None,
    ) -> Optional[Record]:
        """Execute query and fetch first result.

        Args:
            query: SQL query with $1, $2 placeholders
            *args: Query parameters
            timeout: Query timeout (overrides default)

        Returns:
            First result record or None

        Raises:
            RuntimeError: If client not connected
            asyncpg.PostgresError: If query fails
        """
        if not self._connected or self._pool is None:
            raise RuntimeError("TimescaleDB client not connected")

        logger.debug(
            "Executing fetchrow query",
            extra={"query": query, "args": args, "timeout": timeout},
        )

        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)

    async def fetchval(
        self,
        query: str,
        *args: Any,
        column: int = 0,
        timeout: Optional[float] = None,
    ) -> Any:
        """Execute query and fetch single value.

        Args:
            query: SQL query with $1, $2 placeholders
            *args: Query parameters
            column: Column index to return
            timeout: Query timeout (overrides default)

        Returns:
            Single value from result

        Raises:
            RuntimeError: If client not connected
            asyncpg.PostgresError: If query fails
        """
        if not self._connected or self._pool is None:
            raise RuntimeError("TimescaleDB client not connected")

        logger.debug(
            "Executing fetchval query",
            extra={"query": query, "args": args, "column": column, "timeout": timeout},
        )

        async with self._pool.acquire() as conn:
            return await conn.fetchval(query, *args, column=column, timeout=timeout)

    async def execute(
        self,
        query: str,
        *args: Any,
        timeout: Optional[float] = None,
    ) -> str:
        """Execute query without returning results.

        Args:
            query: SQL query with $1, $2 placeholders
            *args: Query parameters
            timeout: Query timeout (overrides default)

        Returns:
            Query status string (e.g., "INSERT 0 1")

        Raises:
            RuntimeError: If client not connected
            asyncpg.PostgresError: If query fails
        """
        if not self._connected or self._pool is None:
            raise RuntimeError("TimescaleDB client not connected")

        logger.debug(
            "Executing query",
            extra={"query": query, "args": args, "timeout": timeout},
        )

        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args, timeout=timeout)

    async def executemany(
        self,
        query: str,
        args: list[tuple[Any, ...]],
        timeout: Optional[float] = None,
    ) -> None:
        """Execute query multiple times with different parameters.

        Args:
            query: SQL query with $1, $2 placeholders
            args: List of parameter tuples
            timeout: Query timeout (overrides default)

        Raises:
            RuntimeError: If client not connected
            asyncpg.PostgresError: If query fails
        """
        if not self._connected or self._pool is None:
            raise RuntimeError("TimescaleDB client not connected")

        logger.debug(
            "Executing executemany",
            extra={"query": query, "count": len(args), "timeout": timeout},
        )

        async with self._pool.acquire() as conn:
            await conn.executemany(query, args, timeout=timeout)

    @property
    def is_connected(self) -> bool:
        """Check if client is connected.

        Returns:
            True if connected, False otherwise
        """
        return self._connected and self._pool is not None
