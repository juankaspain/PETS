"""Gas manager for adaptive EIP-1559 gas pricing.

Provides optimal gas pricing for Polygon network using
Polygon Gas Station API and adaptive strategies.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Optional

import aiohttp
from web3 import Web3

logger = logging.getLogger(__name__)


class GasManager:
    """Manages gas pricing with EIP-1559 adaptive strategies.

    Monitors Polygon Gas Station API and adjusts gas prices
    based on network congestion and urgency requirements.

    Gas strategies:
    - rapid: <30 gwei (urgent trades)
    - fast: 30-50 gwei (normal trades)
    - standard: 50-100 gwei (rebalancing)
    - queue: >100 gwei (wait for lower gas)

    Example:
        >>> manager = GasManager()
        >>> await manager.start()
        >>> gas_price = await manager.get_gas_price(strategy='fast')
        >>> await manager.stop()
    """

    def __init__(
        self,
        gas_station_url: str = "https://gasstation.polygon.technology/v2",
        refresh_interval: int = 10,
        max_priority_fee: int = 30,
    ) -> None:
        """Initialize gas manager.

        Args:
            gas_station_url: Polygon Gas Station API URL
            refresh_interval: Seconds between gas price updates
            max_priority_fee: Maximum priority fee per gas in gwei
        """
        self.gas_station_url = gas_station_url
        self.refresh_interval = refresh_interval
        self.max_priority_fee = Web3.to_wei(max_priority_fee, "gwei")

        self._current_gas: Optional[dict[str, int]] = None
        self._refresh_task: Optional[asyncio.Task[None]] = None
        self._running = False
        self._session: Optional[aiohttp.ClientSession] = None

    async def start(self) -> None:
        """Start gas price monitoring."""
        if self._running:
            logger.warning("GasManager already running")
            return

        logger.info("Starting GasManager", extra={"refresh_interval": self.refresh_interval})
        self._running = True
        self._session = aiohttp.ClientSession()

        # Initial fetch
        await self._fetch_gas_prices()

        # Start refresh task
        self._refresh_task = asyncio.create_task(self._refresh_loop())

        logger.info("GasManager started")

    async def stop(self) -> None:
        """Stop gas price monitoring."""
        if not self._running:
            return

        logger.info("Stopping GasManager")
        self._running = False

        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass

        if self._session:
            await self._session.close()

        logger.info("GasManager stopped")

    async def _fetch_gas_prices(self) -> None:
        """Fetch current gas prices from Polygon Gas Station."""
        if not self._session:
            return

        try:
            async with self._session.get(self.gas_station_url) as response:
                if response.status == 200:
                    data = await response.json()

                    # Parse gas prices (in gwei)
                    self._current_gas = {
                        "safeLow": Web3.to_wei(data["safeLow"]["maxFee"], "gwei"),
                        "standard": Web3.to_wei(data["standard"]["maxFee"], "gwei"),
                        "fast": Web3.to_wei(data["fast"]["maxFee"], "gwei"),
                        "estimatedBaseFee": Web3.to_wei(
                            data["estimatedBaseFee"], "gwei"
                        ),
                    }

                    logger.debug(
                        "Gas prices updated",
                        extra={
                            "safeLow": Web3.from_wei(self._current_gas["safeLow"], "gwei"),
                            "standard": Web3.from_wei(
                                self._current_gas["standard"], "gwei"
                            ),
                            "fast": Web3.from_wei(self._current_gas["fast"], "gwei"),
                        },
                    )
                else:
                    logger.error(
                        "Failed to fetch gas prices",
                        extra={"status": response.status},
                    )
        except Exception as e:
            logger.error("Error fetching gas prices", extra={"error": str(e)})

    async def _refresh_loop(self) -> None:
        """Refresh gas prices periodically."""
        while self._running:
            try:
                await asyncio.sleep(self.refresh_interval)
                await self._fetch_gas_prices()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in gas refresh loop", extra={"error": str(e)})

    async def get_gas_price(
        self, strategy: str = "fast"
    ) -> dict[str, int]:
        """Get gas price for strategy.

        Args:
            strategy: Gas strategy ('rapid', 'fast', 'standard', 'safe')

        Returns:
            Dict with maxFeePerGas and maxPriorityFeePerGas in wei

        Raises:
            ValueError: If gas prices not available

        Example:
            >>> gas = await manager.get_gas_price('fast')
            >>> tx = {
            ...     'maxFeePerGas': gas['maxFeePerGas'],
            ...     'maxPriorityFeePerGas': gas['maxPriorityFeePerGas'],
            ... }
        """
        if self._current_gas is None:
            raise ValueError("Gas prices not available, call start() first")

        base_fee = self._current_gas["estimatedBaseFee"]

        # Strategy mapping
        if strategy == "rapid":
            # Urgent: base + 30 gwei priority
            max_fee = base_fee + Web3.to_wei(30, "gwei")
            priority_fee = self.max_priority_fee
        elif strategy == "fast":
            # Normal: use fast price
            max_fee = self._current_gas["fast"]
            priority_fee = self.max_priority_fee
        elif strategy == "standard":
            # Standard: use standard price
            max_fee = self._current_gas["standard"]
            priority_fee = Web3.to_wei(20, "gwei")
        elif strategy == "safe":
            # Safe: use safeLow price
            max_fee = self._current_gas["safeLow"]
            priority_fee = Web3.to_wei(10, "gwei")
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        return {
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": priority_fee,
        }

    async def should_wait_for_gas(self, max_gwei: int = 100) -> bool:
        """Check if should wait for lower gas prices.

        Args:
            max_gwei: Maximum acceptable gas price in gwei

        Returns:
            True if current gas > max_gwei

        Example:
            >>> if await manager.should_wait_for_gas(max_gwei=50):
            ...     logger.info("Gas too high, waiting...")
            ...     await asyncio.sleep(60)
        """
        if self._current_gas is None:
            return False

        current_gwei = Web3.from_wei(self._current_gas["fast"], "gwei")
        return current_gwei > max_gwei

    async def estimate_gas_cost(
        self, gas_limit: int, strategy: str = "fast"
    ) -> Decimal:
        """Estimate gas cost in MATIC.

        Args:
            gas_limit: Gas limit for transaction
            strategy: Gas strategy

        Returns:
            Estimated cost in MATIC

        Example:
            >>> cost_matic = await manager.estimate_gas_cost(21000, 'fast')
            >>> cost_usdc = cost_matic * matic_price_usd
        """
        gas_price = await self.get_gas_price(strategy)
        cost_wei = gas_limit * gas_price["maxFeePerGas"]
        return Decimal(cost_wei) / Decimal(10**18)

    def get_current_gas_gwei(self) -> Optional[dict[str, float]]:
        """Get current gas prices in gwei.

        Returns:
            Dict of gas prices in gwei or None if not available
        """
        if self._current_gas is None:
            return None

        return {
            "safeLow": float(Web3.from_wei(self._current_gas["safeLow"], "gwei")),
            "standard": float(Web3.from_wei(self._current_gas["standard"], "gwei")),
            "fast": float(Web3.from_wei(self._current_gas["fast"], "gwei")),
            "baseFee": float(
                Web3.from_wei(self._current_gas["estimatedBaseFee"], "gwei")
            ),
        }
