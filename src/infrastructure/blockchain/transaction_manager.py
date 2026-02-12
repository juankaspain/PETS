"""Transaction manager for signing and sending transactions."""

import logging
import time
from typing import Optional

from web3.exceptions import TransactionNotFound

from src.infrastructure.blockchain.gas_estimator import GasEstimator
from src.infrastructure.blockchain.nonce_manager import NonceManager
from src.infrastructure.blockchain.web3_client import Web3Client

logger = logging.getLogger(__name__)


class TransactionManager:
    """Manager for transaction signing and sending.
    
    Handles:
    - Transaction signing with private key
    - Gas estimation and setting
    - Nonce management
    - Transaction sending
    - Confirmation waiting
    - Retry logic
    """

    def __init__(
        self,
        web3_client: Web3Client,
        gas_estimator: GasEstimator,
        nonce_manager: NonceManager,
        max_retries: int = 3,
    ):
        """Initialize transaction manager.
        
        Args:
            web3_client: Web3 client
            gas_estimator: Gas estimator
            nonce_manager: Nonce manager
            max_retries: Max retry attempts
        """
        self.web3_client = web3_client
        self.gas_estimator = gas_estimator
        self.nonce_manager = nonce_manager
        self.max_retries = max_retries
        
        logger.info("TransactionManager initialized")

    async def send_transaction(
        self,
        tx: dict,
        wait_for_receipt: bool = True,
        timeout: int = 120,
    ) -> tuple[str, Optional[dict]]:
        """Send transaction with retry logic.
        
        Args:
            tx: Transaction dict
            wait_for_receipt: Wait for transaction receipt
            timeout: Receipt timeout in seconds
            
        Returns:
            Tuple of (tx_hash, receipt)
        """
        for attempt in range(self.max_retries):
            try:
                # Get nonce
                nonce = await self.nonce_manager.get_next_nonce(self.web3_client.address)
                tx['nonce'] = nonce
                
                # Estimate gas
                gas_params = await self.gas_estimator.estimate_gas(tx)
                tx.update(gas_params)
                
                # Sign transaction
                signed_tx = self.web3_client.account.sign_transaction(tx)
                
                # Send transaction
                tx_hash = self.web3_client.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx_hash_hex = tx_hash.hex()
                
                logger.info(
                    "Transaction sent",
                    extra={
                        "tx_hash": tx_hash_hex,
                        "nonce": nonce,
                        "attempt": attempt + 1,
                    },
                )
                
                # Wait for receipt if requested
                receipt = None
                if wait_for_receipt:
                    try:
                        receipt = self.web3_client.wait_for_transaction(
                            tx_hash_hex,
                            timeout=timeout,
                        )
                        
                        # Check if transaction succeeded
                        if receipt['status'] == 0:
                            raise Exception("Transaction failed (status=0)")
                        
                        # Mark nonce as used
                        await self.nonce_manager.mark_nonce_used(
                            self.web3_client.address,
                            nonce,
                        )
                        
                    except TransactionNotFound:
                        logger.warning(
                            "Transaction not found",
                            extra={"tx_hash": tx_hash_hex},
                        )
                        # Will retry
                        continue
                
                return tx_hash_hex, receipt
                
            except Exception as e:
                logger.error(
                    "Transaction failed",
                    extra={
                        "attempt": attempt + 1,
                        "error": str(e),
                    },
                    exc_info=True,
                )
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
        
        raise Exception(f"Transaction failed after {self.max_retries} attempts")

    async def send_transaction_batch(
        self,
        transactions: list[dict],
    ) -> list[tuple[str, Optional[dict]]]:
        """Send multiple transactions.
        
        Args:
            transactions: List of transaction dicts
            
        Returns:
            List of (tx_hash, receipt) tuples
        """
        results = []
        
        for tx in transactions:
            try:
                tx_hash, receipt = await self.send_transaction(tx)
                results.append((tx_hash, receipt))
            except Exception as e:
                logger.error(
                    "Batch transaction failed",
                    extra={"error": str(e)},
                    exc_info=True,
                )
                results.append((None, None))
        
        return results
