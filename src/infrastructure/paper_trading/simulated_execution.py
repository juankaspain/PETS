"""Simulated order execution engine."""

import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List
from uuid import UUID

from src.infrastructure.paper_trading.paper_wallet import PaperWallet

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order status."""

    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class SimulatedOrder:
    """Simulated order."""

    order_id: UUID
    market_id: str
    side: str  # BUY or SELL
    size: Decimal
    price: Decimal  # Limit price
    post_only: bool
    status: OrderStatus
    created_at: datetime
    filled_size: Decimal = Decimal("0")
    filled_at: datetime | None = None

    def is_fillable(self, market_price: Decimal) -> bool:
        """Check if order can be filled at market price.

        Args:
            market_price: Current market price

        Returns:
            True if order can be filled
        """
        if self.status not in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]:
            return False

        if self.post_only:
            # Post-only orders only fill when market crosses limit (maker)
            if self.side == "BUY":
                # Buy order fills when market price drops to or below limit
                return market_price <= self.price
            else:
                # Sell order fills when market price rises to or above limit
                return market_price >= self.price
        else:
            # Taker orders (not used in PETS - PROHIBITED)
            raise ValueError("Taker orders prohibited in PETS")


class SimulatedExecution:
    """Simulated order execution engine.

    Matches orders against market prices and fills them in paper wallet.
    """

    def __init__(self, paper_wallet: PaperWallet):
        """Initialize simulated execution engine.

        Args:
            paper_wallet: Paper wallet instance
        """
        self.paper_wallet = paper_wallet
        self.orders: Dict[UUID, SimulatedOrder] = {}
        self.maker_rebate_rate = Decimal("0.002")  # 20 bps

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
            side: Order side (BUY or SELL)
            size: Order size
            price: Limit price
            post_only: Post-only flag (default True)

        Returns:
            Order ID

        Raises:
            ValueError: If post_only is False (taker orders prohibited)
        """
        if not post_only:
            raise ValueError("Taker orders prohibited in PETS - post_only must be True")

        # Place order in paper wallet (reserves balance)
        order_id = self.paper_wallet.place_order(market_id, side, size, price)

        # Create simulated order
        order = SimulatedOrder(
            order_id=order_id,
            market_id=market_id,
            side=side,
            size=size,
            price=price,
            post_only=post_only,
            status=OrderStatus.OPEN,
            created_at=datetime.utcnow(),
        )

        self.orders[order_id] = order

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

    def process_market_update(
        self,
        market_id: str,
        current_price: Decimal,
    ) -> List[UUID]:
        """Process market price update and fill matching orders.

        Args:
            market_id: Market ID
            current_price: Current market price

        Returns:
            List of filled order IDs
        """
        filled_orders = []

        for order in self.orders.values():
            if order.market_id != market_id:
                continue

            if order.is_fillable(current_price):
                # Fill order at limit price (not market price - post-only maker)
                fill_price = order.price

                # Fill in paper wallet
                position_id = self.paper_wallet.fill_order(
                    order_id=order.order_id,
                    market_id=market_id,
                    side=order.side,
                    size=order.size,
                    fill_price=fill_price,
                    maker_rebate_rate=self.maker_rebate_rate,
                )

                # Update order status
                order.status = OrderStatus.FILLED
                order.filled_size = order.size
                order.filled_at = datetime.utcnow()

                filled_orders.append(order.order_id)

                logger.info(
                    "Order filled",
                    extra={
                        "order_id": str(order.order_id),
                        "position_id": str(position_id),
                        "fill_price": float(fill_price),
                        "market_price": float(current_price),
                    },
                )

        return filled_orders

    def cancel_order(self, order_id: UUID) -> None:
        """Cancel order.

        Args:
            order_id: Order ID

        Raises:
            ValueError: If order not found or already filled
        """
        order = self.orders.get(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            raise ValueError(f"Order {order_id} already {order.status.value}")

        # Return reserved balance if BUY order
        if order.side == "BUY":
            refund = order.size * order.price
            self.paper_wallet.balance += refund

        order.status = OrderStatus.CANCELLED

        logger.info(
            "Order cancelled",
            extra={"order_id": str(order_id)},
        )

    def get_order(self, order_id: UUID) -> SimulatedOrder | None:
        """Get order by ID.

        Args:
            order_id: Order ID

        Returns:
            Order or None
        """
        return self.orders.get(order_id)

    def get_open_orders(self, market_id: str | None = None) -> List[SimulatedOrder]:
        """Get open orders.

        Args:
            market_id: Optional market ID filter

        Returns:
            List of open orders
        """
        orders = [
            order
            for order in self.orders.values()
            if order.status in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]
        ]

        if market_id:
            orders = [order for order in orders if order.market_id == market_id]

        return orders
