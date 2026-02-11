"""Wallet repository implementation with Redis cache.

Provides fast access to wallet balances and nonces using Redis.
"""

import json
import logging
from decimal import Decimal
from typing import Optional

from src.infrastructure.persistence.redis_client import RedisClient

logger = logging.getLogger(__name__)


class WalletRepository:
    """Wallet repository with Redis cache.

    Uses Redis for fast access to wallet data.
    No persistent storage - data is synced from blockchain.

    Provides:
    - Balance tracking (USDC, MATIC)
    - Nonce management
    - Real-time updates
    - Fast access (<1ms)

    Example:
        >>> repo = WalletRepository(redis_client)
        >>> await repo.update_balance(
        ...     address="0x123...",
        ...     token="USDC",
        ...     balance=Decimal("10000"),
        ... )
        >>> balance = await repo.get_balance("0x123...", "USDC")
    """

    def __init__(self, redis_client: RedisClient) -> None:
        """Initialize wallet repository.

        Args:
            redis_client: Connected Redis client
        """
        self.redis = redis_client

    def _balance_key(self, address: str, token: str) -> str:
        """Generate cache key for balance."""
        return f"wallet:{address.lower()}:balance:{token.upper()}"

    def _nonce_key(self, address: str) -> str:
        """Generate cache key for nonce."""
        return f"wallet:{address.lower()}:nonce"

    def _wallet_key(self, address: str) -> str:
        """Generate cache key for wallet metadata."""
        return f"wallet:{address.lower()}"

    async def update_balance(
        self,
        address: str,
        token: str,
        balance: Decimal,
        ttl: int = 300,
    ) -> None:
        """Update wallet balance.

        Args:
            address: Wallet address
            token: Token symbol (USDC, MATIC)
            balance: Balance amount
            ttl: Cache TTL in seconds
        """
        key = self._balance_key(address, token)
        await self.redis.setex(key, ttl, str(balance))

        logger.debug(
            "Wallet balance updated",
            extra={"address": address, "token": token, "balance": str(balance)},
        )

    async def get_balance(
        self,
        address: str,
        token: str,
    ) -> Optional[Decimal]:
        """Get wallet balance.

        Args:
            address: Wallet address
            token: Token symbol

        Returns:
            Balance or None if not cached
        """
        key = self._balance_key(address, token)
        balance_str = await self.redis.get(key)

        if balance_str is None:
            return None

        return Decimal(balance_str)

    async def update_nonce(
        self,
        address: str,
        nonce: int,
    ) -> None:
        """Update wallet nonce.

        Args:
            address: Wallet address
            nonce: Current nonce
        """
        key = self._nonce_key(address)
        await self.redis.set(key, nonce)

        logger.debug(
            "Wallet nonce updated",
            extra={"address": address, "nonce": nonce},
        )

    async def get_nonce(self, address: str) -> Optional[int]:
        """Get wallet nonce.

        Args:
            address: Wallet address

        Returns:
            Nonce or None if not cached
        """
        key = self._nonce_key(address)
        nonce_str = await self.redis.get(key)

        if nonce_str is None:
            return None

        return int(nonce_str)

    async def update_wallet_metadata(
        self,
        address: str,
        metadata: dict,
        ttl: int = 300,
    ) -> None:
        """Update wallet metadata.

        Args:
            address: Wallet address
            metadata: Metadata dict
            ttl: Cache TTL in seconds
        """
        key = self._wallet_key(address)
        await self.redis.setex(key, ttl, json.dumps(metadata))

        logger.debug(
            "Wallet metadata updated",
            extra={"address": address},
        )

    async def get_wallet_metadata(self, address: str) -> Optional[dict]:
        """Get wallet metadata.

        Args:
            address: Wallet address

        Returns:
            Metadata dict or None
        """
        key = self._wallet_key(address)
        data = await self.redis.get(key)

        if data is None:
            return None

        return json.loads(data)
