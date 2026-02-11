"""Wallet monitor for balance alerts and transaction tracking.

Provides real-time monitoring of wallet balances and transactions
with configurable alerts.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Optional, Callable, Awaitable

from web3 import Web3
from web3.types import HexBytes

logger = logging.getLogger(__name__)

AlertCallback = Callable[[str, dict], Awaitable[None]]


class WalletMonitor:
    """Monitors wallet balances and transactions.

    Provides:
    - Balance alerts (warning/critical thresholds)
    - Transaction monitoring with bump logic
    - Stuck transaction detection
    - Audit trail

    Example:
        >>> async def on_alert(alert_type: str, data: dict) -> None:
        ...     logger.warning(f"Alert: {alert_type}", extra=data)
        >>>
        >>> monitor = WalletMonitor(web3, address, on_alert)
        >>> await monitor.start()
        >>> await monitor.track_transaction(tx_hash)
        >>> await monitor.stop()
    """

    def __init__(
        self,
        web3: Web3,
        address: str,
        alert_callback: AlertCallback,
        usdc_warning_threshold: Decimal = Decimal("2500"),
        usdc_critical_threshold: Decimal = Decimal("1000"),
        matic_warning_threshold: Decimal = Decimal("10"),
        matic_critical_threshold: Decimal = Decimal("5"),
        check_interval: int = 60,
        tx_bump_threshold: int = 120,
        tx_stuck_threshold: int = 600,
    ) -> None:
        """Initialize wallet monitor.

        Args:
            web3: Web3 instance
            address: Wallet address to monitor
            alert_callback: Async callback for alerts
            usdc_warning_threshold: USDC warning level
            usdc_critical_threshold: USDC critical level
            matic_warning_threshold: MATIC warning level
            matic_critical_threshold: MATIC critical level
            check_interval: Balance check interval in seconds
            tx_bump_threshold: Seconds before bumping pending tx gas
            tx_stuck_threshold: Seconds before marking tx as stuck
        """
        self.web3 = web3
        self.address = Web3.to_checksum_address(address)
        self.alert_callback = alert_callback

        self.usdc_warning = usdc_warning_threshold
        self.usdc_critical = usdc_critical_threshold
        self.matic_warning = matic_warning_threshold
        self.matic_critical = matic_critical_threshold

        self.check_interval = check_interval
        self.tx_bump_threshold = tx_bump_threshold
        self.tx_stuck_threshold = tx_stuck_threshold

        self._monitor_task: Optional[asyncio.Task[None]] = None
        self._running = False
        self._tracked_txs: dict[str, float] = {}  # tx_hash -> timestamp

    async def start(self) -> None:
        """Start wallet monitoring."""
        if self._running:
            logger.warning("WalletMonitor already running")
            return

        logger.info(
            "Starting WalletMonitor",
            extra={
                "address": self.address,
                "check_interval": self.check_interval,
            },
        )
        self._running = True

        self._monitor_task = asyncio.create_task(self._monitor_loop())

        logger.info("WalletMonitor started")

    async def stop(self) -> None:
        """Stop wallet monitoring."""
        if not self._running:
            return

        logger.info("Stopping WalletMonitor")
        self._running = False

        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("WalletMonitor stopped")

    async def check_balance(
        self, token_address: Optional[str] = None
    ) -> Decimal:
        """Check balance and trigger alerts if needed.

        Args:
            token_address: ERC20 token address (None = MATIC)

        Returns:
            Current balance
        """
        if token_address is None:
            # Native MATIC balance
            balance_wei = await self.web3.eth.get_balance(self.address)
            balance = Decimal(balance_wei) / Decimal(10**18)

            # Check thresholds
            if balance < self.matic_critical:
                await self.alert_callback(
                    "balance_critical",
                    {
                        "address": self.address,
                        "token": "MATIC",
                        "balance": float(balance),
                        "threshold": float(self.matic_critical),
                    },
                )
            elif balance < self.matic_warning:
                await self.alert_callback(
                    "balance_warning",
                    {
                        "address": self.address,
                        "token": "MATIC",
                        "balance": float(balance),
                        "threshold": float(self.matic_warning),
                    },
                )
        else:
            # ERC20 token (assume USDC with 6 decimals for now)
            # In production, fetch decimals from contract
            token_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=ERC20_ABI,
            )
            balance_raw = await token_contract.functions.balanceOf(self.address).call()
            balance = Decimal(balance_raw) / Decimal(10**6)  # USDC decimals

            # Check thresholds
            if balance < self.usdc_critical:
                await self.alert_callback(
                    "balance_critical",
                    {
                        "address": self.address,
                        "token": "USDC",
                        "balance": float(balance),
                        "threshold": float(self.usdc_critical),
                    },
                )
            elif balance < self.usdc_warning:
                await self.alert_callback(
                    "balance_warning",
                    {
                        "address": self.address,
                        "token": "USDC",
                        "balance": float(balance),
                        "threshold": float(self.usdc_warning),
                    },
                )

        return balance

    async def track_transaction(self, tx_hash: HexBytes) -> None:
        """Track transaction for monitoring.

        Args:
            tx_hash: Transaction hash

        Example:
            >>> tx_hash = await wallet_manager.submit_transaction(...)
            >>> await monitor.track_transaction(tx_hash)
        """
        import time

        tx_hash_str = tx_hash.hex() if isinstance(tx_hash, HexBytes) else tx_hash
        self._tracked_txs[tx_hash_str] = time.time()

        logger.info(
            "Transaction tracked",
            extra={"tx_hash": tx_hash_str, "address": self.address},
        )

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                # Check balances
                await self.check_balance()  # MATIC
                # Note: In production, iterate through all token addresses

                # Check tracked transactions
                await self._check_transactions()

                await asyncio.sleep(self.check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in monitor loop", extra={"error": str(e)})

    async def _check_transactions(self) -> None:
        """Check status of tracked transactions."""
        import time

        current_time = time.time()
        to_remove = []

        for tx_hash, start_time in self._tracked_txs.items():
            try:
                # Get transaction receipt
                receipt = await self.web3.eth.get_transaction_receipt(tx_hash)

                if receipt is not None:
                    # Transaction mined
                    logger.info(
                        "Transaction mined",
                        extra={
                            "tx_hash": tx_hash,
                            "block": receipt["blockNumber"],
                            "status": receipt["status"],
                        },
                    )
                    to_remove.append(tx_hash)
                else:
                    # Still pending
                    pending_time = current_time - start_time

                    if pending_time > self.tx_stuck_threshold:
                        # Transaction stuck
                        await self.alert_callback(
                            "transaction_stuck",
                            {
                                "tx_hash": tx_hash,
                                "address": self.address,
                                "pending_seconds": int(pending_time),
                            },
                        )
                        to_remove.append(tx_hash)

                    elif pending_time > self.tx_bump_threshold:
                        # Consider bumping gas
                        await self.alert_callback(
                            "transaction_slow",
                            {
                                "tx_hash": tx_hash,
                                "address": self.address,
                                "pending_seconds": int(pending_time),
                                "suggestion": "bump_gas",
                            },
                        )

            except Exception as e:
                logger.error(
                    "Error checking transaction",
                    extra={"tx_hash": tx_hash, "error": str(e)},
                )

        # Remove completed/stuck transactions
        for tx_hash in to_remove:
            del self._tracked_txs[tx_hash]


# Minimal ERC20 ABI for balanceOf
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
]
