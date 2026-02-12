"""Fee calculator domain service."""

from decimal import Decimal


class FeeCalculator:
    """Fee calculator for Polymarket trading fees.

    Polymarket fee structure:
    - Taker fees: 0% to 3.15% based on volume
    - Maker rebate: 20% (negative fee)
    - Post-only orders: MAKER REBATE

    Volume tiers (30-day):
    - $0 - $1K: 0% taker
    - $1K - $10K: 1.05% taker
    - $10K - $100K: 2.10% taker
    - $100K - $1M: 2.625% taker
    - $1M - $10M: 3.15% taker
    - >$10M: 3.15% taker

    Example:
        >>> calc = FeeCalculator()
        >>> fee = calc.calculate_maker_rebate(Decimal("1000"))
        >>> fee
        Decimal('-200.00')  # 20% rebate = -$200
    """

    # Maker rebate (negative fee)
    MAKER_REBATE_PCT = Decimal("-0.20")  # 20% rebate

    # Taker fee tiers
    TAKER_FEES = [
        (Decimal("0"), Decimal("0.0000")),  # $0-$1K: 0%
        (Decimal("1000"), Decimal("0.0105")),  # $1K-$10K: 1.05%
        (Decimal("10000"), Decimal("0.0210")),  # $10K-$100K: 2.10%
        (Decimal("100000"), Decimal("0.02625")),  # $100K-$1M: 2.625%
        (Decimal("1000000"), Decimal("0.0315")),  # >$1M: 3.15%
    ]

    @staticmethod
    def calculate_maker_rebate(trade_value: Decimal) -> Decimal:
        """Calculate maker rebate for post-only order.

        Args:
            trade_value: Trade value in USDC

        Returns:
            Rebate amount (negative = earning)

        Example:
            >>> FeeCalculator.calculate_maker_rebate(Decimal("1000"))
            Decimal('-200.00')  # Earn $200 rebate
        """
        return trade_value * FeeCalculator.MAKER_REBATE_PCT

    @staticmethod
    def calculate_taker_fee(
        trade_value: Decimal,
        volume_30d: Decimal,
    ) -> Decimal:
        """Calculate taker fee.

        Args:
            trade_value: Trade value in USDC
            volume_30d: 30-day volume for tier

        Returns:
            Fee amount (positive = cost)

        Note:
            NEVER used in PETS - all orders post-only.
        """
        # Find tier
        fee_pct = FeeCalculator.TAKER_FEES[-1][1]  # Default to highest
        for threshold, pct in FeeCalculator.TAKER_FEES:
            if volume_30d < threshold:
                break
            fee_pct = pct

        return trade_value * fee_pct

    @staticmethod
    def calculate_net_fee(
        trade_value: Decimal,
        post_only: bool = True,
        volume_30d: Decimal = Decimal("0"),
    ) -> Decimal:
        """Calculate net fee for trade.

        Args:
            trade_value: Trade value in USDC
            post_only: Post-only order (default True)
            volume_30d: 30-day volume

        Returns:
            Net fee (negative = rebate, positive = cost)

        Example:
            >>> FeeCalculator.calculate_net_fee(Decimal("1000"))
            Decimal('-200.00')  # Post-only earns rebate
        """
        if post_only:
            return FeeCalculator.calculate_maker_rebate(trade_value)
        else:
            return FeeCalculator.calculate_taker_fee(trade_value, volume_30d)

    @staticmethod
    def calculate_break_even_price_adjustment(
        entry_price: Decimal,
        post_only: bool = True,
    ) -> Decimal:
        """Calculate price adjustment needed to break even after fees.

        Args:
            entry_price: Entry price
            post_only: Post-only order

        Returns:
            Price delta to break even

        Example:
            >>> FeeCalculator.calculate_break_even_price_adjustment(
            ...     Decimal("0.50"),
            ...     post_only=True,
            ... )
            Decimal('-0.20')  # Need 20% favorable movement with rebates
        """
        if post_only:
            # With maker rebate, break even is easier
            # Need to overcome spread, but rebate helps
            rebate_pct = abs(FeeCalculator.MAKER_REBATE_PCT)
            return -entry_price * rebate_pct
        else:
            # With taker fee, need to overcome fee
            # Approximate with 2% taker fee
            return entry_price * Decimal("0.02")
