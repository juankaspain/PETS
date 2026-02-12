"""Web3 client for Polygon blockchain."""

import logging
from decimal import Decimal

from web3 import Web3
from web3.middleware import geth_poa_middleware

from src.domain.value_objects.private_key import PrivateKey

logger = logging.getLogger(__name__)


class Web3Client:
    """Client for Polygon blockchain operations.
    
    Handles:
    - Connection to Polygon RPC
    - Account management
    - Balance queries
    - Transaction sending
    """

    def __init__(self, rpc_url: str, private_key: PrivateKey):
        """Initialize Web3 client.
        
        Args:
            rpc_url: Polygon RPC URL
            private_key: Wallet private key
        """
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Polygon is PoS (Proof of Authority), need middleware
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Load account from private key
        self.account = self.w3.eth.account.from_key(private_key.value)
        self.address = self.account.address
        
        # Verify connection
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to {rpc_url}")
        
        logger.info(
            "Web3Client initialized",
            extra={
                "network": self.w3.eth.chain_id,
                "address": self.address,
                "block_number": self.w3.eth.block_number,
            },
        )

    def get_balance(self) -> Decimal:
        """Get MATIC balance.
        
        Returns:
            MATIC balance
        """
        balance_wei = self.w3.eth.get_balance(self.address)
        balance_matic = Decimal(self.w3.from_wei(balance_wei, 'ether'))
        return balance_matic

    def get_usdc_balance(self, usdc_address: str) -> Decimal:
        """Get USDC balance.
        
        Args:
            usdc_address: USDC token contract address
            
        Returns:
            USDC balance
        """
        # USDC uses 6 decimals
        usdc_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function",
            }
        ]
        
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(usdc_address),
            abi=usdc_abi,
        )
        
        balance_raw = contract.functions.balanceOf(self.address).call()
        balance_usdc = Decimal(balance_raw) / Decimal(10**6)
        
        return balance_usdc

    def get_current_block(self) -> int:
        """Get current block number.
        
        Returns:
            Current block number
        """
        return self.w3.eth.block_number

    def get_transaction_receipt(self, tx_hash: str) -> dict:
        """Get transaction receipt.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction receipt
        """
        return self.w3.eth.get_transaction_receipt(tx_hash)

    def wait_for_transaction(
        self,
        tx_hash: str,
        timeout: int = 120,
        poll_latency: float = 0.5,
    ) -> dict:
        """Wait for transaction to be mined.
        
        Args:
            tx_hash: Transaction hash
            timeout: Timeout in seconds
            poll_latency: Poll interval in seconds
            
        Returns:
            Transaction receipt
        """
        logger.info(
            "Waiting for transaction",
            extra={"tx_hash": tx_hash, "timeout": timeout},
        )
        
        receipt = self.w3.eth.wait_for_transaction_receipt(
            tx_hash,
            timeout=timeout,
            poll_latency=poll_latency,
        )
        
        logger.info(
            "Transaction mined",
            extra={
                "tx_hash": tx_hash,
                "block": receipt['blockNumber'],
                "status": receipt['status'],
            },
        )
        
        return receipt
