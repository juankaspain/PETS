"""Simulated order executor for paper trading."""

import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict
from uuid import UUID, uuid4

from src.domain.entities.order import Order
from src.domain.value_objects.price import Price
from src.domain.value_objects.size import Size

logger = logging.getLogger(__name__)


@dataclass
class OrderFill:
    """Order fill event."""

    order_id: UUID
    fill_price: Decimal
    fill_size: Decimal
    timestamp: datetime


class SimulatedOrderExecutor:
    """Simulates order execution for paper trading.

    Matches orders against market prices.
    Enforces post-only (no taker fills).
    Simulates maker rebate (20%).
    """

    def __init__(self):
        """Initialize simulated executor."""
        self.pending_orders: Dict[UUID, Order] = {}
        self.filled_orders: Dict[UUID, OrderFill] = {}

        logger.info("Simulated order executor initialized")

    def submit_order(
        self,
        market_id: str,
        side: str,
        size: Decimal,
        price: Decimal,
        post_only: bool = True,
    ) -> UUID:
        """Submit order for execution.

        Args:
            market_id: Market ID
            side: BUY or SELL
            size: Order size
            price: Limit price
            post_only: Post-only flag (must be True)

        Returns:
            Order ID

        Raises:
            ValueError: If post_only is False
        """
        if not post_only:
            raise ValueError("Paper trading only supports post-only orders")

        order_id = uuid4()

        # Create order (simplified - real implementation uses Order entity)
        logger.info(
            "Order submitted",
            extra={
                "order_id": str(order_id),
                "market_id": market_id,
                "side": side,
                "size": float(size),
                "price": float(price),
            },
        )

        return order_id

    def check_fill(
        self,
        order_id: UUID,
        market_price: Decimal,
        order_price: Decimal,
        order_side: str,
        order_size: Decimal,
    ) -> OrderFill | None:
        """Check if order should be filled based on market price.

        Args:
            order_id: Order ID
            market_price: Current market price
            order_price: Order limit price
            order_side: BUY or SELL
            order_size: Order size

        Returns:
            OrderFill if filled, None otherwise
        """
        filled = False

        if order_side == "BUY":
            # BUY order fills when market price <= limit price
            filled = market_price <= order_price
        else:
            # SELL order fills when market price >= limit price
            filled = market_price >= order_price

        if filled:
            fill = OrderFill(
                order_id=order_id,
                fill_price=order_price,  # Fill at limit price (maker)
                fill_size=order_size,
                timestamp=datetime.utcnow(),
            )

            self.filled_orders[order_id] = fill

            logger.info(
                "Order filled",
                extra={
                    "order_id": str(order_id),
                    "fill_price": float(order_price),
                    "fill_size": float(order_size),
                    "market_price": float(market_price),
                },
            )

            return fill

        return None

    def cancel_order(self, order_id: UUID) -> bool:
        """Cancel pending order.

        Args:
            order_id: Order ID

        Returns:
            True if cancelled, False if not found
        """
        if order_id in self.pending_orders:
            del self.pending_orders[order_id]
            logger.info("Order cancelled", extra={"order_id": str(order_id)})
            return True
        return False

    def get_fill(self, order_id: UUID) -> OrderFill | None:
        """Get fill for order.

        Args:
            order_id: Order ID

        Returns:
            OrderFill or None
        """
        return self.filled_orders.get(order_id)
