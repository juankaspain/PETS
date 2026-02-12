"""Gas estimator domain service."""

from decimal import Decimal


class GasEstimator:
    """Gas estimator for Polygon transactions.

    Typical gas costs on Polygon:
    - ERC20 transfer: ~65K gas
    - ERC20 approve: ~46K gas
    - Trade execution: ~120K gas
    - Complex trade: ~180K gas

    Example:
        >>> estimator = GasEstimator()
        >>> gas_limit = estimator.estimate_trade_gas()
        >>> gas_limit
        144000  # 120K * 1.2 buffer
    """

    # Gas estimates (in gas units)
    GAS_TRANSFER = 65_000
    GAS_APPROVE = 46_000
    GAS_TRADE = 120_000
    GAS_COMPLEX_TRADE = 180_000

    # Safety buffer (20%)
    SAFETY_BUFFER = Decimal("1.20")

    @staticmethod
    def estimate_trade_gas(complex: bool = False) -> int:
        """Estimate gas for trade execution.

        Args:
            complex: Complex trade with multiple operations

        Returns:
            Gas limit with safety buffer

        Example:
            >>> GasEstimator.estimate_trade_gas()
            144000
            >>> GasEstimator.estimate_trade_gas(complex=True)
            216000
        """
        base_gas = (
            GasEstimator.GAS_COMPLEX_TRADE if complex else GasEstimator.GAS_TRADE
        )
        return int(base_gas * GasEstimator.SAFETY_BUFFER)

    @staticmethod
    def estimate_approve_gas() -> int:
        """Estimate gas for ERC20 approve.

        Returns:
            Gas limit with safety buffer
        """
        return int(GasEstimator.GAS_APPROVE * GasEstimator.SAFETY_BUFFER)

    @staticmethod
    def estimate_transfer_gas() -> int:
        """Estimate gas for ERC20 transfer.

        Returns:
            Gas limit with safety buffer
        """
        return int(GasEstimator.GAS_TRANSFER * GasEstimator.SAFETY_BUFFER)

    @staticmethod
    def calculate_gas_cost_matic(
        gas_limit: int,
        gas_price_gwei: Decimal,
    ) -> Decimal:
        """Calculate gas cost in MATIC.

        Args:
            gas_limit: Gas limit
            gas_price_gwei: Gas price in gwei

        Returns:
            Gas cost in MATIC

        Example:
            >>> GasEstimator.calculate_gas_cost_matic(
            ...     gas_limit=144000,
            ...     gas_price_gwei=Decimal("30"),
            ... )
            Decimal('0.00432')  # MATIC
        """
        # Convert gwei to MATIC
        gas_price_matic = gas_price_gwei / Decimal("1000000000")
        return Decimal(gas_limit) * gas_price_matic

    @staticmethod
    def calculate_gas_cost_usdc(
        gas_limit: int,
        gas_price_gwei: Decimal,
        matic_price_usdc: Decimal,
    ) -> Decimal:
        """Calculate gas cost in USDC.

        Args:
            gas_limit: Gas limit
            gas_price_gwei: Gas price in gwei
            matic_price_usdc: MATIC price in USDC

        Returns:
            Gas cost in USDC

        Example:
            >>> GasEstimator.calculate_gas_cost_usdc(
            ...     gas_limit=144000,
            ...     gas_price_gwei=Decimal("30"),
            ...     matic_price_usdc=Decimal("0.80"),
            ... )
            Decimal('0.003456')  # USDC
        """
        cost_matic = GasEstimator.calculate_gas_cost_matic(gas_limit, gas_price_gwei)
        return cost_matic * matic_price_usdc

    @staticmethod
    def optimize_gas_limit(estimated_gas: int, max_gas: int = 500_000) -> int:
        """Optimize gas limit.

        Args:
            estimated_gas: Estimated gas needed
            max_gas: Maximum gas limit

        Returns:
            Optimized gas limit

        Logic:
        - Add 20% buffer
        - Cap at max_gas
        - Min 21000 (ETH transfer minimum)
        """
        with_buffer = int(estimated_gas * GasEstimator.SAFETY_BUFFER)
        return max(21_000, min(with_buffer, max_gas))
