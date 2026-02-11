"""Polygon RPC client wrapper for Web3.py.

Provides simplified Web3 interface with connection pooling
and helper methods.
"""

import logging
from decimal import Decimal
from typing import Optional

from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.types import Wei

logger = logging.getLogger(__name__)


class PolygonRPCClient:
    """Polygon RPC client using Web3.py.

    Provides:
    - Connection pooling
    - Gas estimation helpers
    - ERC20 token helpers
    - Transaction monitoring

    Example:
        >>> client = PolygonRPCClient(rpc_url=url)
        >>> await client.connect()
        >>> balance = await client.get_balance(address)
        >>> await client.close()
    """

    def __init__(
        self,
        rpc_url: str,
        request_timeout: int = 30,
    ) -> None:
        """Initialize Polygon RPC client.

        Args:
            rpc_url: Polygon RPC URL (Alchemy/Infura/etc)
            request_timeout: Request timeout in seconds
        """
        self.rpc_url = rpc_url
        self.request_timeout = request_timeout
        self._web3: Optional[AsyncWeb3] = None

    async def connect(self) -> None:
        """Connect to Polygon RPC."""
        if self._web3 is not None:
            logger.warning("PolygonRPCClient already connected")
            return

        provider = AsyncHTTPProvider(
            self.rpc_url,
            request_kwargs={"timeout": self.request_timeout},
        )
        self._web3 = AsyncWeb3(provider)

        # Verify connection
        is_connected = await self._web3.is_connected()
        if not is_connected:
            raise RuntimeError("Failed to connect to Polygon RPC")

        chain_id = await self._web3.eth.chain_id
        logger.info(
            "PolygonRPCClient connected",
            extra={"chain_id": chain_id, "rpc_url": self.rpc_url},
        )

    async def close(self) -> None:
        """Close RPC connection."""
        if self._web3 is not None:
            # AsyncWeb3 doesn't have explicit close
            self._web3 = None
            logger.info("PolygonRPCClient closed")

    @property
    def web3(self) -> AsyncWeb3:
        """Get Web3 instance.

        Returns:
            AsyncWeb3 instance

        Raises:
            RuntimeError: If not connected
        """
        if self._web3 is None:
            raise RuntimeError("Client not connected")
        return self._web3

    async def get_balance(
        self, address: str, block: str = "latest"
    ) -> Decimal:
        """Get native token balance (MATIC).

        Args:
            address: Wallet address
            block: Block identifier

        Returns:
            Balance in MATIC
        """
        balance_wei = await self.web3.eth.get_balance(address, block)
        return Decimal(balance_wei) / Decimal(10**18)

    async def get_transaction_count(
        self, address: str, block: str = "pending"
    ) -> int:
        """Get transaction count (nonce).

        Args:
            address: Wallet address
            block: Block identifier

        Returns:
            Transaction count
        """
        return await self.web3.eth.get_transaction_count(address, block)

    async def estimate_gas(
        self, transaction: dict
    ) -> int:
        """Estimate gas for transaction.

        Args:
            transaction: Transaction dict

        Returns:
            Estimated gas limit
        """
        return await self.web3.eth.estimate_gas(transaction)

    async def get_gas_price(self) -> Wei:
        """Get current gas price.

        Returns:
            Gas price in wei
        """
        return await self.web3.eth.gas_price

    async def send_raw_transaction(self, signed_tx: bytes) -> str:
        """Send signed transaction.

        Args:
            signed_tx: Signed transaction bytes

        Returns:
            Transaction hash
        """
        tx_hash = await self.web3.eth.send_raw_transaction(signed_tx)
        return tx_hash.hex()

    async def wait_for_transaction(
        self, tx_hash: str, timeout: int = 120
    ) -> dict:
        """Wait for transaction to be mined.

        Args:
            tx_hash: Transaction hash
            timeout: Timeout in seconds

        Returns:
            Transaction receipt
        """
        receipt = await self.web3.eth.wait_for_transaction_receipt(
            tx_hash, timeout=timeout
        )
        return dict(receipt)
