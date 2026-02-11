"""Wallet manager for hot/cold wallet operations.

Provides secure wallet management with hot/cold separation,
auto-rebalancing, and local transaction signing.

SECURITY: Private keys are NEVER logged or sent over network.
"""

import logging
from decimal import Decimal
from typing import Optional

from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3
from web3.types import TxParams, HexBytes

from src.infrastructure.wallet.gas_manager import GasManager
from src.infrastructure.wallet.nonce_manager import NonceManager

logger = logging.getLogger(__name__)

# Security: Disable eth_account warnings about unaudited HDWallet
Account.enable_unaudited_hdwallet_features()


class WalletManager:
    """Manages hot and cold wallets with auto-rebalancing.

    Hot wallet: 10-20% of capital, used for active trading
    Cold wallet: 80-90% of capital, manual access only

    Security:
    - Private keys stored encrypted (see WalletRecovery)
    - Transaction signing LOCAL only
    - NEVER logs private keys
    - NEVER sends private keys over network

    Example:
        >>> manager = WalletManager(
        ...     web3=web3,
        ...     hot_private_key=hot_key,
        ...     cold_address=cold_addr,
        ...     nonce_manager=nonce_mgr,
        ...     gas_manager=gas_mgr,
        ... )
        >>> balance = await manager.get_hot_balance()
        >>> await manager.auto_rebalance(min_threshold=Decimal('1000'))
    """

    def __init__(
        self,
        web3: Web3,
        hot_private_key: str,
        cold_address: str,
        nonce_manager: NonceManager,
        gas_manager: GasManager,
        hot_min_ratio: Decimal = Decimal("0.10"),
        hot_max_ratio: Decimal = Decimal("0.20"),
        auto_rebalance_threshold: Decimal = Decimal("0.05"),
    ) -> None:
        """Initialize wallet manager.

        Args:
            web3: Web3 instance connected to Polygon
            hot_private_key: Hot wallet private key (will NOT be logged)
            cold_address: Cold wallet address (0x...)
            nonce_manager: Nonce manager for transaction coordination
            gas_manager: Gas manager for optimal gas pricing
            hot_min_ratio: Minimum hot wallet ratio (default 10%)
            hot_max_ratio: Maximum hot wallet ratio (default 20%)
            auto_rebalance_threshold: Trigger rebalance if below (default 5%)
        """
        self.web3 = web3
        self.nonce_manager = nonce_manager
        self.gas_manager = gas_manager
        self.cold_address = Web3.to_checksum_address(cold_address)

        # Create hot wallet account (SECURITY: Never log this)
        self.hot_account: LocalAccount = Account.from_key(hot_private_key)
        self.hot_address = self.hot_account.address

        # Wallet ratios
        self.hot_min_ratio = hot_min_ratio
        self.hot_max_ratio = hot_max_ratio
        self.auto_rebalance_threshold = auto_rebalance_threshold

        logger.info(
            "WalletManager initialized",
            extra={
                "hot_address": self.hot_address,
                "cold_address": self.cold_address,
                "hot_min_ratio": float(hot_min_ratio),
                "hot_max_ratio": float(hot_max_ratio),
            },
        )

    async def get_hot_balance(self, token_address: Optional[str] = None) -> Decimal:
        """Get hot wallet balance.

        Args:
            token_address: ERC20 token address (None = native MATIC)

        Returns:
            Balance in token units

        Example:
            >>> usdc_balance = await manager.get_hot_balance(USDC_ADDRESS)
            >>> matic_balance = await manager.get_hot_balance()
        """
        if token_address is None:
            # Native MATIC balance
            balance_wei = await self.web3.eth.get_balance(self.hot_address)
            return Decimal(balance_wei) / Decimal(10**18)
        else:
            # ERC20 token balance (USDC has 6 decimals)
            token_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=ERC20_ABI,
            )
            balance = await token_contract.functions.balanceOf(self.hot_address).call()
            decimals = await token_contract.functions.decimals().call()
            return Decimal(balance) / Decimal(10**decimals)

    async def get_cold_balance(self, token_address: Optional[str] = None) -> Decimal:
        """Get cold wallet balance.

        Args:
            token_address: ERC20 token address (None = native MATIC)

        Returns:
            Balance in token units
        """
        if token_address is None:
            balance_wei = await self.web3.eth.get_balance(self.cold_address)
            return Decimal(balance_wei) / Decimal(10**18)
        else:
            token_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=ERC20_ABI,
            )
            balance = await token_contract.functions.balanceOf(self.cold_address).call()
            decimals = await token_contract.functions.decimals().call()
            return Decimal(balance) / Decimal(10**decimals)

    async def get_total_balance(
        self, token_address: Optional[str] = None
    ) -> tuple[Decimal, Decimal, Decimal]:
        """Get total balance across hot and cold wallets.

        Args:
            token_address: ERC20 token address (None = native MATIC)

        Returns:
            Tuple of (hot_balance, cold_balance, total_balance)
        """
        hot = await self.get_hot_balance(token_address)
        cold = await self.get_cold_balance(token_address)
        return hot, cold, hot + cold

    async def check_rebalance_needed(
        self, token_address: str
    ) -> tuple[bool, Decimal, Decimal]:
        """Check if rebalancing is needed.

        Args:
            token_address: ERC20 token address to check

        Returns:
            Tuple of (needs_rebalance, current_ratio, target_ratio)

        Example:
            >>> needed, current, target = await manager.check_rebalance_needed(USDC_ADDRESS)
            >>> if needed:
            ...     await manager.auto_rebalance(USDC_ADDRESS)
        """
        hot, cold, total = await self.get_total_balance(token_address)

        if total == Decimal("0"):
            return False, Decimal("0"), self.hot_min_ratio

        current_ratio = hot / total

        # Need rebalance if below threshold
        if current_ratio < self.auto_rebalance_threshold:
            return True, current_ratio, self.hot_min_ratio

        return False, current_ratio, self.hot_min_ratio

    async def auto_rebalance(
        self,
        token_address: str,
        min_threshold: Optional[Decimal] = None,
    ) -> Optional[HexBytes]:
        """Auto-rebalance from cold to hot wallet if needed.

        Args:
            token_address: ERC20 token address
            min_threshold: Minimum balance before rebalancing (default: auto_rebalance_threshold)

        Returns:
            Transaction hash if rebalance executed, None otherwise

        Raises:
            ValueError: If insufficient cold wallet balance

        Example:
            >>> tx_hash = await manager.auto_rebalance(USDC_ADDRESS)
            >>> if tx_hash:
            ...     logger.info(f"Rebalance tx: {tx_hash.hex()}")
        """
        min_threshold = min_threshold or self.auto_rebalance_threshold
        hot, cold, total = await self.get_total_balance(token_address)

        if total == Decimal("0"):
            logger.warning("Cannot rebalance: zero total balance")
            return None

        current_ratio = hot / total

        if current_ratio >= min_threshold:
            logger.debug(
                "Rebalance not needed",
                extra={
                    "current_ratio": float(current_ratio),
                    "threshold": float(min_threshold),
                },
            )
            return None

        # Calculate target amount for hot wallet
        target_hot = total * self.hot_min_ratio
        transfer_amount = target_hot - hot

        if transfer_amount <= Decimal("0"):
            return None

        if cold < transfer_amount:
            raise ValueError(
                f"Insufficient cold wallet balance: {cold} < {transfer_amount}"
            )

        logger.info(
            "Auto-rebalancing wallets",
            extra={
                "from": "cold",
                "to": "hot",
                "amount": float(transfer_amount),
                "current_ratio": float(current_ratio),
                "target_ratio": float(self.hot_min_ratio),
            },
        )

        # NOTE: This requires manual intervention - cold wallet not managed by bot
        # In production, this would trigger an alert for manual cold wallet transfer
        logger.warning(
            "Manual cold wallet transfer required",
            extra={
                "from_address": self.cold_address,
                "to_address": self.hot_address,
                "token_address": token_address,
                "amount": float(transfer_amount),
            },
        )

        return None

    async def sign_transaction(self, transaction: TxParams) -> HexBytes:
        """Sign transaction with hot wallet.

        SECURITY: Signing happens locally, private key never leaves this function.

        Args:
            transaction: Transaction parameters

        Returns:
            Signed transaction bytes

        Example:
            >>> tx = {'to': '0x...', 'value': 1000, 'gas': 21000, ...}
            >>> signed = await manager.sign_transaction(tx)
        """
        signed = self.hot_account.sign_transaction(transaction)
        return signed.rawTransaction

    async def submit_transaction(
        self,
        to_address: str,
        value: int = 0,
        data: bytes = b"",
        gas_limit: Optional[int] = None,
    ) -> HexBytes:
        """Build, sign, and submit transaction.

        Args:
            to_address: Recipient address
            value: Value in wei (default 0)
            data: Transaction data (default empty)
            gas_limit: Gas limit (None = estimate)

        Returns:
            Transaction hash

        Raises:
            Exception: If transaction fails

        Example:
            >>> tx_hash = await manager.submit_transaction(
            ...     to_address='0x...',
            ...     value=Web3.to_wei(1, 'ether'),
            ... )
        """
        # Get nonce
        nonce = await self.nonce_manager.get_next_nonce(self.hot_address)

        # Get gas price
        gas_price = await self.gas_manager.get_gas_price()

        # Build transaction
        transaction: TxParams = {
            "from": self.hot_address,
            "to": Web3.to_checksum_address(to_address),
            "value": value,
            "data": data,
            "nonce": nonce,
            "maxFeePerGas": gas_price["maxFeePerGas"],
            "maxPriorityFeePerGas": gas_price["maxPriorityFeePerGas"],
            "chainId": await self.web3.eth.chain_id,
        }

        # Estimate gas if not provided
        if gas_limit is None:
            gas_limit = await self.web3.eth.estimate_gas(transaction)
        transaction["gas"] = gas_limit

        # Sign transaction
        signed_tx = await self.sign_transaction(transaction)

        # Submit transaction
        tx_hash = await self.web3.eth.send_raw_transaction(signed_tx)

        logger.info(
            "Transaction submitted",
            extra={
                "tx_hash": tx_hash.hex(),
                "from": self.hot_address,
                "to": to_address,
                "value": value,
                "nonce": nonce,
                "gas_limit": gas_limit,
            },
        )

        return tx_hash


# Minimal ERC20 ABI for balance and decimals
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
]
