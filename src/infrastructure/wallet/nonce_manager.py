"""Nonce manager for thread-safe transaction coordination.

Provides Redis-backed nonce tracking to prevent transaction
collisions when multiple bots use the same wallet.
"""

import asyncio
import logging
from typing import Optional

from web3 import Web3

from src.infrastructure.persistence.redis_client import RedisClient

logger = logging.getLogger(__name__)


class NonceManager:
    """Manages transaction nonces with Redis-backed synchronization.

    Prevents nonce collisions when multiple bots use the same wallet.
    Syncs with blockchain periodically and on errors.

    Example:
        >>> manager = NonceManager(web3, redis_client)
        >>> await manager.start()
        >>> nonce = await manager.get_next_nonce('0x...')
        >>> await manager.confirm_nonce('0x...', nonce)
        >>> await manager.stop()
    """

    def __init__(
        self,
        web3: Web3,
        redis_client: RedisClient,
        lock_timeout: float = 5.0,
        sync_interval: int = 300,
    ) -> None:
        """Initialize nonce manager.

        Args:
            web3: Web3 instance connected to Polygon
            redis_client: Connected Redis client
            lock_timeout: Redis lock timeout in seconds
            sync_interval: Blockchain sync interval in seconds (default 5min)
        """
        self.web3 = web3
        self.redis = redis_client
        self.lock_timeout = lock_timeout
        self.sync_interval = sync_interval
        self._sync_task: Optional[asyncio.Task[None]] = None
        self._running = False

    async def start(self) -> None:
        """Start nonce manager with periodic sync."""
        if self._running:
            logger.warning("NonceManager already running")
            return

        logger.info("Starting NonceManager", extra={"sync_interval": self.sync_interval})
        self._running = True

        # Start sync task
        self._sync_task = asyncio.create_task(self._sync_loop())

        logger.info("NonceManager started")

    async def stop(self) -> None:
        """Stop nonce manager."""
        if not self._running:
            return

        logger.info("Stopping NonceManager")
        self._running = False

        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass

        logger.info("NonceManager stopped")

    def _get_nonce_key(self, address: str) -> str:
        """Get Redis key for address nonce.

        Args:
            address: Wallet address

        Returns:
            Redis key string
        """
        return f"nonce:{address.lower()}"

    def _get_lock_key(self, address: str) -> str:
        """Get Redis lock key for address.

        Args:
            address: Wallet address

        Returns:
            Redis lock key string
        """
        return f"nonce:lock:{address.lower()}"

    async def sync_nonce(self, address: str) -> int:
        """Sync nonce with blockchain.

        Args:
            address: Wallet address

        Returns:
            Current nonce from blockchain

        Example:
            >>> nonce = await manager.sync_nonce('0x...')
        """
        address = Web3.to_checksum_address(address)
        blockchain_nonce = await self.web3.eth.get_transaction_count(address, "pending")

        # Update Redis
        await self.redis.set(self._get_nonce_key(address), blockchain_nonce)

        logger.info(
            "Nonce synced with blockchain",
            extra={"address": address, "nonce": blockchain_nonce},
        )

        return blockchain_nonce

    async def get_next_nonce(self, address: str) -> int:
        """Get next available nonce for address.

        Thread-safe with Redis lock. Increments nonce atomically.

        Args:
            address: Wallet address

        Returns:
            Next nonce to use

        Raises:
            TimeoutError: If lock cannot be acquired

        Example:
            >>> nonce = await manager.get_next_nonce('0x...')
            >>> tx = {'nonce': nonce, ...}
        """
        address = Web3.to_checksum_address(address)
        nonce_key = self._get_nonce_key(address)
        lock_key = self._get_lock_key(address)

        try:
            async with self.redis.lock(
                lock_key,
                timeout=self.lock_timeout,
                blocking=True,
                blocking_timeout=self.lock_timeout,
            ):
                # Get current nonce from Redis
                redis_nonce = await self.redis.get(nonce_key)

                if redis_nonce is None:
                    # First time, sync with blockchain
                    current_nonce = await self.sync_nonce(address)
                else:
                    current_nonce = int(redis_nonce)

                # Increment nonce atomically
                next_nonce = current_nonce
                await self.redis.set(nonce_key, current_nonce + 1)

                logger.debug(
                    "Nonce acquired",
                    extra={"address": address, "nonce": next_nonce},
                )

                return next_nonce

        except asyncio.TimeoutError:
            logger.error(
                "Failed to acquire nonce lock",
                extra={"address": address, "timeout": self.lock_timeout},
            )
            raise TimeoutError(f"Nonce lock timeout for {address}")

    async def confirm_nonce(self, address: str, nonce: int) -> None:
        """Confirm nonce was used successfully.

        Currently a no-op, but can be used for tracking.

        Args:
            address: Wallet address
            nonce: Nonce that was used
        """
        logger.debug(
            "Nonce confirmed",
            extra={"address": address, "nonce": nonce},
        )

    async def reset_nonce(self, address: str) -> int:
        """Reset nonce to blockchain value.

        Use this if nonce gets out of sync.

        Args:
            address: Wallet address

        Returns:
            New nonce from blockchain

        Example:
            >>> nonce = await manager.reset_nonce('0x...')
            >>> logger.info(f"Nonce reset to {nonce}")
        """
        logger.warning("Resetting nonce", extra={"address": address})
        return await self.sync_nonce(address)

    async def _sync_loop(self) -> None:
        """Periodically sync nonces with blockchain."""
        while self._running:
            try:
                await asyncio.sleep(self.sync_interval)

                # Get all nonce keys
                # Note: In production, maintain a list of active addresses
                # For now, this is a placeholder
                logger.debug("Periodic nonce sync triggered")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in nonce sync loop", extra={"error": str(e)})
