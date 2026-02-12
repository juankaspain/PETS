"""Nonce manager using Redis for atomic increments."""

import logging

from src.infrastructure.persistence.redis_client import RedisClient

logger = logging.getLogger(__name__)


class NonceManager:
    """Manager for transaction nonce tracking.
    
    Uses Redis for:
    - Atomic nonce increment
    - Prevent concurrent nonce conflicts
    - Track pending transactions
    - Detect nonce gaps
    """

    def __init__(self, redis: RedisClient, web3_client):
        """Initialize nonce manager.
        
        Args:
            redis: Redis client
            web3_client: Web3 client for on-chain nonce
        """
        self.redis = redis
        self.web3_client = web3_client
        self.prefix = "nonce:"
        
        logger.info("NonceManager initialized")

    async def get_next_nonce(self, address: str) -> int:
        """Get next nonce for address.
        
        Args:
            address: Wallet address
            
        Returns:
            Next nonce to use
        """
        key = f"{self.prefix}{address}"
        
        # Get current nonce from Redis
        stored_nonce = await self.redis.get(key)
        
        if stored_nonce is None:
            # First time, get from blockchain
            on_chain_nonce = self.web3_client.w3.eth.get_transaction_count(address)
            await self.redis.set(key, str(on_chain_nonce))
            nonce = on_chain_nonce
        else:
            # Atomic increment in Redis
            nonce = await self.redis.incr(key)
        
        logger.info(
            "Nonce allocated",
            extra={"address": address, "nonce": nonce},
        )
        
        return nonce

    async def mark_nonce_used(self, address: str, nonce: int) -> None:
        """Mark nonce as successfully used.
        
        Args:
            address: Wallet address
            nonce: Nonce that was used
        """
        # Store in used set
        used_key = f"{self.prefix}{address}:used"
        await self.redis.sadd(used_key, str(nonce))
        
        logger.debug(
            "Nonce marked used",
            extra={"address": address, "nonce": nonce},
        )

    async def detect_nonce_gap(self, address: str) -> list[int]:
        """Detect gaps in nonce sequence.
        
        Args:
            address: Wallet address
            
        Returns:
            List of missing nonces
        """
        key = f"{self.prefix}{address}"
        used_key = f"{self.prefix}{address}:used"
        
        # Get current nonce and used nonces
        current = int(await self.redis.get(key) or 0)
        used_nonces = await self.redis.smembers(used_key)
        used_set = {int(n) for n in used_nonces}
        
        # Find gaps
        gaps = [n for n in range(current) if n not in used_set]
        
        if gaps:
            logger.warning(
                "Nonce gaps detected",
                extra={"address": address, "gaps": gaps},
            )
        
        return gaps

    async def reset_nonce(self, address: str) -> None:
        """Reset nonce to on-chain value.
        
        Args:
            address: Wallet address
        """
        on_chain_nonce = self.web3_client.w3.eth.get_transaction_count(address)
        
        key = f"{self.prefix}{address}"
        await self.redis.set(key, str(on_chain_nonce))
        
        logger.info(
            "Nonce reset",
            extra={"address": address, "nonce": on_chain_nonce},
        )
