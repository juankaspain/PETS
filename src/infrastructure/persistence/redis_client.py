"""Redis client with connection pool and pub/sub support.

Provides async Redis operations for caching, pub/sub messaging,
and distributed locks.
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional, Union

import redis.asyncio as redis
from redis.asyncio import Redis, ConnectionPool
from redis.asyncio.lock import Lock

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client with connection pooling.

    Provides caching, pub/sub messaging, and distributed locks.
    Supports JSON serialization for complex data types.

    Example:
        >>> client = RedisClient(url="redis://localhost:6379/0")
        >>> await client.connect()
        >>> await client.set("key", {"value": 123}, ttl=60)
        >>> data = await client.get("key")
        >>> await client.close()
    """

    def __init__(
        self,
        url: str,
        max_connections: int = 100,
        min_idle_connections: int = 10,
        decode_responses: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize Redis client.

        Args:
            url: Redis connection URL (redis://host:port/db)
            max_connections: Maximum connection pool size
            min_idle_connections: Minimum idle connections
            decode_responses: Decode byte responses to strings
            **kwargs: Additional Redis client parameters
        """
        self.url = url
        self.max_connections = max_connections
        self.min_idle_connections = min_idle_connections
        self.decode_responses = decode_responses
        self.kwargs = kwargs
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None
        self._connected = False

    async def connect(self) -> None:
        """Create Redis connection pool.

        Raises:
            redis.RedisError: If connection fails
        """
        if self._connected:
            logger.warning("Redis already connected")
            return

        logger.info(
            "Connecting to Redis",
            extra={
                "max_connections": self.max_connections,
                "min_idle": self.min_idle_connections,
            },
        )

        self._pool = ConnectionPool.from_url(
            url=self.url,
            max_connections=self.max_connections,
            decode_responses=self.decode_responses,
            **self.kwargs,
        )
        self._client = Redis(connection_pool=self._pool)
        self._connected = True

        logger.info("Redis connected successfully")

    async def close(self) -> None:
        """Close Redis connection pool gracefully."""
        if not self._connected or self._client is None:
            return

        logger.info("Closing Redis connection pool")
        await self._client.close()
        if self._pool is not None:
            await self._pool.disconnect()
        self._connected = False
        logger.info("Redis connection pool closed")

    async def health_check(self) -> bool:
        """Check Redis health.

        Returns:
            True if Redis is healthy, False otherwise
        """
        if not self._connected or self._client is None:
            return False

        try:
            await self._client.ping()
            return True
        except Exception as e:
            logger.error("Redis health check failed", extra={"error": str(e)})
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis.

        Args:
            key: Redis key

        Returns:
            Deserialized value or None if not found

        Raises:
            RuntimeError: If client not connected
            redis.RedisError: If operation fails
        """
        if not self._connected or self._client is None:
            raise RuntimeError("Redis client not connected")

        value = await self._client.get(key)
        if value is None:
            return None

        try:
            return json.loads(value) if isinstance(value, str) else value
        except json.JSONDecodeError:
            return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in Redis.

        Args:
            key: Redis key
            value: Value to store (will be JSON serialized if dict/list)
            ttl: Time-to-live in seconds (None = no expiration)

        Returns:
            True if successful

        Raises:
            RuntimeError: If client not connected
            redis.RedisError: If operation fails
        """
        if not self._connected or self._client is None:
            raise RuntimeError("Redis client not connected")

        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        result = await self._client.set(key, value, ex=ttl)
        return bool(result)

    async def delete(self, *keys: str) -> int:
        """Delete keys from Redis.

        Args:
            *keys: Keys to delete

        Returns:
            Number of keys deleted

        Raises:
            RuntimeError: If client not connected
            redis.RedisError: If operation fails
        """
        if not self._connected or self._client is None:
            raise RuntimeError("Redis client not connected")

        return await self._client.delete(*keys)

    async def exists(self, *keys: str) -> int:
        """Check if keys exist.

        Args:
            *keys: Keys to check

        Returns:
            Number of existing keys

        Raises:
            RuntimeError: If client not connected
            redis.RedisError: If operation fails
        """
        if not self._connected or self._client is None:
            raise RuntimeError("Redis client not connected")

        return await self._client.exists(*keys)

    async def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration.

        Args:
            key: Redis key
            seconds: Expiration time in seconds

        Returns:
            True if timeout was set

        Raises:
            RuntimeError: If client not connected
            redis.RedisError: If operation fails
        """
        if not self._connected or self._client is None:
            raise RuntimeError("Redis client not connected")

        return await self._client.expire(key, seconds)

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment key value.

        Args:
            key: Redis key
            amount: Increment amount

        Returns:
            New value after increment

        Raises:
            RuntimeError: If client not connected
            redis.RedisError: If operation fails
        """
        if not self._connected or self._client is None:
            raise RuntimeError("Redis client not connected")

        return await self._client.incrby(key, amount)

    @asynccontextmanager
    async def lock(
        self,
        name: str,
        timeout: float = 5.0,
        blocking: bool = True,
        blocking_timeout: Optional[float] = None,
    ) -> AsyncIterator[Lock]:
        """Acquire distributed lock.

        Args:
            name: Lock name
            timeout: Lock timeout in seconds
            blocking: Block until lock acquired
            blocking_timeout: Max time to wait for lock

        Yields:
            Redis lock object

        Raises:
            RuntimeError: If client not connected
            redis.LockError: If lock cannot be acquired

        Example:
            >>> async with client.lock("nonce:0xabc", timeout=5.0) as lock:
            ...     nonce = await get_nonce()
            ...     await increment_nonce()
        """
        if not self._connected or self._client is None:
            raise RuntimeError("Redis client not connected")

        lock_obj = self._client.lock(
            name=name,
            timeout=timeout,
            blocking=blocking,
            blocking_timeout=blocking_timeout,
        )

        async with lock_obj:
            yield lock_obj

    async def publish(self, channel: str, message: Any) -> int:
        """Publish message to channel.

        Args:
            channel: Channel name
            message: Message to publish (will be JSON serialized if dict/list)

        Returns:
            Number of subscribers that received message

        Raises:
            RuntimeError: If client not connected
            redis.RedisError: If operation fails
        """
        if not self._connected or self._client is None:
            raise RuntimeError("Redis client not connected")

        if isinstance(message, (dict, list)):
            message = json.dumps(message)

        return await self._client.publish(channel, message)

    async def subscribe(self, *channels: str) -> redis.client.PubSub:
        """Subscribe to channels.

        Args:
            *channels: Channel names to subscribe

        Returns:
            PubSub object for receiving messages

        Raises:
            RuntimeError: If client not connected

        Example:
            >>> pubsub = await client.subscribe("events.orders")
            >>> async for message in pubsub.listen():
            ...     if message["type"] == "message":
            ...         data = json.loads(message["data"])
            ...         await handle_message(data)
        """
        if not self._connected or self._client is None:
            raise RuntimeError("Redis client not connected")

        pubsub = self._client.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub

    @property
    def is_connected(self) -> bool:
        """Check if client is connected.

        Returns:
            True if connected, False otherwise
        """
        return self._connected and self._client is not None
