"""EIP-1559 gas estimator for Polygon."""

import logging
from decimal import Decimal

from web3 import Web3

from src.infrastructure.blockchain.web3_client import Web3Client

logger = logging.getLogger(__name__)


class GasEstimator:
    """EIP-1559 gas estimator.
    
    Handles:
    - Base fee estimation
    - Priority fee estimation
    - Max fee calculation
    - Gas limit estimation
    - Buffer application
    """

    def __init__(
        self,
        web3_client: Web3Client,
        max_gas_price_gwei: Decimal = Decimal("100"),
        gas_price_buffer: Decimal = Decimal("1.1"),
    ):
        """Initialize gas estimator.
        
        Args:
            web3_client: Web3 client
            max_gas_price_gwei: Max gas price cap in Gwei
            gas_price_buffer: Buffer multiplier (1.1 = 10% buffer)
        """
        self.web3_client = web3_client
        self.max_gas_price_gwei = max_gas_price_gwei
        self.gas_price_buffer = gas_price_buffer
        
        logger.info(
            "GasEstimator initialized",
            extra={
                "max_gas_price_gwei": float(max_gas_price_gwei),
                "gas_price_buffer": float(gas_price_buffer),
            },
        )

    async def estimate_gas(self, tx: dict) -> dict:
        """Estimate gas for transaction.
        
        Args:
            tx: Transaction dict
            
        Returns:
            Gas parameters dict with:
            - gas: Gas limit
            - maxFeePerGas: Max fee per gas (wei)
            - maxPriorityFeePerGas: Max priority fee per gas (wei)
        """
        # Get base fee from latest block
        latest_block = self.web3_client.w3.eth.get_block('latest')
        base_fee = latest_block['baseFeePerGas']
        
        # Estimate priority fee (tip to miners)
        # For Polygon, typically 30-50 Gwei
        priority_fee = Web3.to_wei(30, 'gwei')
        
        # Calculate max fee (base + priority)
        # Apply buffer for base fee fluctuation
        max_fee = int(Decimal(base_fee) * self.gas_price_buffer) + priority_fee
        
        # Apply max gas price cap
        max_allowed = Web3.to_wei(self.max_gas_price_gwei, 'gwei')
        if max_fee > max_allowed:
            logger.warning(
                "Gas price exceeds cap",
                extra={
                    "max_fee_gwei": Web3.from_wei(max_fee, 'gwei'),
                    "cap_gwei": float(self.max_gas_price_gwei),
                },
            )
            max_fee = max_allowed
            priority_fee = min(priority_fee, max_allowed)
        
        # Estimate gas limit
        try:
            gas_limit = self.web3_client.w3.eth.estimate_gas(tx)
            # Add 20% buffer for safety
            gas_limit = int(Decimal(gas_limit) * Decimal("1.2"))
        except Exception as e:
            logger.warning(
                "Gas estimation failed, using default",
                extra={"error": str(e)},
            )
            gas_limit = 300000  # Default for CLOB operations
        
        logger.info(
            "Gas estimated",
            extra={
                "base_fee_gwei": Web3.from_wei(base_fee, 'gwei'),
                "priority_fee_gwei": Web3.from_wei(priority_fee, 'gwei'),
                "max_fee_gwei": Web3.from_wei(max_fee, 'gwei'),
                "gas_limit": gas_limit,
            },
        )
        
        return {
            "gas": gas_limit,
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": priority_fee,
        }

    def calculate_gas_cost(
        self,
        gas_used: int,
        gas_price_wei: int,
    ) -> Decimal:
        """Calculate gas cost in MATIC.
        
        Args:
            gas_used: Gas units used
            gas_price_wei: Gas price in wei
            
        Returns:
            Gas cost in MATIC
        """
        cost_wei = gas_used * gas_price_wei
        cost_matic = Decimal(Web3.from_wei(cost_wei, 'ether'))
        return cost_matic
