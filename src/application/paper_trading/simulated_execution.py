"""Simulated order execution for paper trading."""

import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class SimulatedExecution:
    """Simulated order execution engine.
    
    Matches paper orders against market prices to simulate fills.
    - Post-only orders only (no taker)
    - Slippage = 0 (maker orders)
    - Maker rebate 20% applied
    - No blockchain transactions
    """

    def __init__(self):
        """Initialize simulated execution engine."""
        pass

    def should_fill(
        self,
        side: str,
        limit_price: Decimal,
        market_price: Decimal,
        post_only: bool = True,
    ) -> bool:
        """Check if order should be filled.
        
        Args:
            side: Order side (BUY or SELL)
            limit_price: Order limit price
            market_price: Current market price
            post_only: Post-only flag
            
        Returns:
            True if order should fill
        """
        if post_only:
            # Post-only orders only fill if limit is better than market
            if side == "BUY":
                # Buy limit must be at or above market to be maker
                return limit_price >= market_price
            else:
                # Sell limit must be at or below market to be maker
                return limit_price <= market_price
        else:
            # Taker orders (not used in Bot 8)
            if side == "BUY":
                return market_price <= limit_price
            else:
                return market_price >= limit_price

    def get_fill_price(
        self,
        side: str,
        limit_price: Decimal,
        market_price: Decimal,
        post_only: bool = True,
    ) -> Decimal:
        """Get fill price for order.
        
        Args:
            side: Order side
            limit_price: Order limit price
            market_price: Current market price
            post_only: Post-only flag
            
        Returns:
            Fill price (always limit price for post-only)
        """
        if post_only:
            # Post-only orders fill at limit price (maker)
            return limit_price
        else:
            # Taker orders fill at market price
            return market_price

    def calculate_fees(
        self,
        size: Decimal,
        price: Decimal,
        is_maker: bool = True,
    ) -> Decimal:
        """Calculate trading fees.
        
        Args:
            size: Trade size
            price: Trade price
            is_maker: Is maker order
            
        Returns:
            Fee amount (negative = rebate)
        """
        gross_amount = size * price
        
        if is_maker:
            # Maker rebate: -0.2%
            fee_rate = Decimal("-0.002")
        else:
            # Taker fee: 0% for first tier (not used)
            fee_rate = Decimal("0")
        
        return gross_amount * fee_rate
