"""Paper trading engine for risk-free strategy testing.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import uuid4

from src.domain.entities.order import Order, OrderSide, OrderStatus, OrderType
from src.domain.entities.position import Position, PositionSide

logger = logging.getLogger(__name__)


@dataclass
class PaperTradingConfig:
    """Paper trading configuration."""

    initial_balance: float = 5000.0
    simulate_slippage: bool = True
    simulate_fees: bool = True
    simulate_latency_ms: int = 50
    
    # Fee structure (Polymarket)
    maker_fee_pct: float = 0.0   # 0% maker fee
    taker_fee_pct: float = 0.02  # 2% taker fee
    
    # Slippage parameters
    avg_slippage_bps: float = 10.0  # 0.1% average slippage
    max_slippage_bps: float = 50.0  # 0.5% max slippage


@dataclass
class VirtualBalance:
    """Virtual balance state."""

    available: float
    reserved: float = 0.0
    
    @property
    def total(self) -> float:
        """Total balance."""
        return self.available + self.reserved


@dataclass
class VirtualPosition:
    """Virtual position for paper trading."""

    position_id: str
    market_id: str
    side: PositionSide
    size: float
    entry_price: float
    current_price: float
    opened_at: datetime
    bot_id: int
    
    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L."""
        if self.side == PositionSide.YES:
            return (self.current_price - self.entry_price) * self.size
        else:
            return (self.entry_price - self.current_price) * self.size
    
    @property
    def value(self) -> float:
        """Current position value."""
        return self.current_price * self.size


class PaperTradingEngine:
    """Paper trading engine for risk-free strategy testing.
    
    Simulates:
    - Order execution with realistic fills
    - Slippage based on market conditions
    - Fees (Polymarket: 0% maker, 2% taker)
    - Latency (configurable delay)
    - Position management
    - P&L tracking
    
    Examples:
        >>> config = PaperTradingConfig(initial_balance=5000.0)
        >>> engine = PaperTradingEngine(bot_id=8, config=config)
        >>> await engine.place_order(
        ...     market_id="market_123",
        ...     side=OrderSide.YES,
        ...     size=100.0,
        ...     price=0.65,
        ...     order_type=OrderType.POST_ONLY,
        ... )
    """

    def __init__(
        self,
        bot_id: int,
        config: Optional[PaperTradingConfig] = None,
    ) -> None:
        """Initialize paper trading engine.
        
        Args:
            bot_id: Bot ID for tracking
            config: Paper trading configuration
        """
        self._bot_id = bot_id
        self._config = config or PaperTradingConfig()
        
        # Virtual state
        self._balance = VirtualBalance(
            available=self._config.initial_balance
        )
        self._positions: Dict[str, VirtualPosition] = {}
        self._orders: Dict[str, Order] = {}
        self._fills: List[Dict] = []
        
        # Performance tracking
        self._realized_pnl = 0.0
        self._total_fees_paid = 0.0
        
        logger.info(
            f"Paper trading engine initialized for bot {bot_id} "
            f"with ${self._config.initial_balance:,.2f}"
        )

    @property
    def balance(self) -> VirtualBalance:
        """Get current balance."""
        return self._balance

    @property
    def positions(self) -> List[VirtualPosition]:
        """Get all open positions."""
        return list(self._positions.values())

    @property
    def total_pnl(self) -> float:
        """Calculate total P&L (realized + unrealized)."""
        unrealized = sum(p.unrealized_pnl for p in self._positions.values())
        return self._realized_pnl + unrealized

    @property
    def portfolio_value(self) -> float:
        """Calculate total portfolio value."""
        return self._balance.total + self.total_pnl

    async def place_order(
        self,
        market_id: str,
        side: OrderSide,
        size: float,
        price: float,
        order_type: OrderType,
    ) -> Order:
        """Place virtual order.
        
        Args:
            market_id: Market ID
            side: Order side (YES/NO)
            size: Order size (shares)
            price: Limit price
            order_type: Order type (POST_ONLY recommended)
        
        Returns:
            Order object
        
        Raises:
            ValueError: If insufficient balance
        """
        # Validate balance
        required_capital = size * price
        if required_capital > self._balance.available:
            raise ValueError(
                f"Insufficient balance: need ${required_capital:.2f}, "
                f"have ${self._balance.available:.2f}"
            )
        
        # Create order
        order_id = str(uuid4())
        order = Order(
            order_id=order_id,
            bot_id=self._bot_id,
            market_id=market_id,
            side=side,
            size=Decimal(str(size)),
            price=Decimal(str(price)),
            order_type=order_type,
            status=OrderStatus.PENDING,
            created_at=datetime.now(),
            zone=1,  # Simplified for paper trading
        )
        
        # Reserve capital
        self._balance.available -= required_capital
        self._balance.reserved += required_capital
        
        self._orders[order_id] = order
        
        logger.info(
            f"Placed paper order {order_id[:8]}: {side.value} {size} @ {price}"
        )
        
        # Simulate order execution
        asyncio.create_task(self._simulate_order_execution(order))
        
        return order

    async def cancel_order(self, order_id: str) -> None:
        """Cancel pending order.
        
        Args:
            order_id: Order ID to cancel
        """
        order = self._orders.get(order_id)
        if not order:
            raise ValueError(f"Order not found: {order_id}")
        
        if order.status != OrderStatus.PENDING:
            raise ValueError(
                f"Cannot cancel order in status: {order.status.value}"
            )
        
        # Release reserved capital
        reserved_amount = float(order.size * order.price)
        self._balance.reserved -= reserved_amount
        self._balance.available += reserved_amount
        
        order.status = OrderStatus.CANCELED
        
        logger.info(f"Canceled paper order {order_id[:8]}")

    async def close_position(self, position_id: str) -> float:
        """Close virtual position.
        
        Args:
            position_id: Position ID to close
        
        Returns:
            Realized P&L
        """
        position = self._positions.get(position_id)
        if not position:
            raise ValueError(f"Position not found: {position_id}")
        
        # Calculate final P&L
        pnl = position.unrealized_pnl
        
        # Simulate closing order execution
        if self._config.simulate_slippage:
            slippage_pct = random.uniform(
                -self._config.avg_slippage_bps / 10000,
                self._config.avg_slippage_bps / 10000,
            )
            pnl *= (1 + slippage_pct)
        
        # Apply fees if configured
        if self._config.simulate_fees:
            fee = position.value * self._config.taker_fee_pct
            pnl -= fee
            self._total_fees_paid += fee
        
        # Update balance
        self._balance.available += position.value + pnl
        self._realized_pnl += pnl
        
        # Remove position
        del self._positions[position_id]
        
        logger.info(
            f"Closed paper position {position_id[:8]}: "
            f"P&L ${pnl:+.2f}"
        )
        
        return pnl

    async def _simulate_order_execution(self, order: Order) -> None:
        """Simulate order execution.
        
        Args:
            order: Order to simulate
        """
        # Simulate latency
        if self._config.simulate_latency_ms > 0:
            await asyncio.sleep(self._config.simulate_latency_ms / 1000)
        
        # POST_ONLY orders: simulate no immediate fill
        if order.order_type == OrderType.POST_ONLY:
            # 70% chance of eventual fill for maker orders
            if random.random() < 0.7:
                # Wait additional time for maker fill
                await asyncio.sleep(random.uniform(1.0, 5.0))
                await self._execute_order(order)
            else:
                # Order remains pending (not filled)
                logger.debug(
                    f"POST_ONLY order {order.order_id[:8]} pending (no fill yet)"
                )
        else:
            # MARKET/LIMIT orders fill immediately (simplified)
            await self._execute_order(order)

    async def _execute_order(self, order: Order) -> None:
        """Execute order and create position.
        
        Args:
            order: Order to execute
        """
        # Calculate execution price with slippage
        exec_price = float(order.price)
        
        if self._config.simulate_slippage:
            slippage_bps = random.uniform(
                0,
                self._config.max_slippage_bps,
            )
            slippage_pct = slippage_bps / 10000
            
            if order.side == OrderSide.YES:
                exec_price *= (1 + slippage_pct)  # Pay more
            else:
                exec_price *= (1 - slippage_pct)  # Receive less
        
        # Calculate fees
        fee = 0.0
        if self._config.simulate_fees:
            # POST_ONLY = maker (0%), others = taker (2%)
            fee_rate = (
                self._config.maker_fee_pct
                if order.order_type == OrderType.POST_ONLY
                else self._config.taker_fee_pct
            )
            fee = float(order.size) * exec_price * fee_rate
            self._total_fees_paid += fee
        
        # Create position
        position_id = str(uuid4())
        position = VirtualPosition(
            position_id=position_id,
            market_id=order.market_id,
            side=PositionSide.YES if order.side == OrderSide.YES else PositionSide.NO,
            size=float(order.size),
            entry_price=exec_price,
            current_price=exec_price,
            opened_at=datetime.now(),
            bot_id=self._bot_id,
        )
        
        # Update state
        reserved_amount = float(order.size * order.price)
        self._balance.reserved -= reserved_amount
        self._balance.available -= fee  # Deduct fee
        
        self._positions[position_id] = position
        order.status = OrderStatus.FILLED
        
        # Log fill
        self._fills.append({
            "order_id": order.order_id,
            "position_id": position_id,
            "exec_price": exec_price,
            "fee": fee,
            "timestamp": datetime.now(),
        })
        
        logger.info(
            f"Filled paper order {order.order_id[:8]}: "
            f"{order.side.value} {order.size} @ {exec_price:.4f}, fee ${fee:.2f}"
        )

    def get_performance_summary(self) -> Dict:
        """Get performance summary.
        
        Returns:
            Dictionary with performance metrics
        """
        return {
            "initial_balance": self._config.initial_balance,
            "current_balance": self._balance.total,
            "portfolio_value": self.portfolio_value,
            "realized_pnl": self._realized_pnl,
            "unrealized_pnl": sum(
                p.unrealized_pnl for p in self._positions.values()
            ),
            "total_pnl": self.total_pnl,
            "total_fees": self._total_fees_paid,
            "open_positions": len(self._positions),
            "total_fills": len(self._fills),
            "roi": (
                (self.portfolio_value - self._config.initial_balance)
                / self._config.initial_balance
            ),
        }

    def reset(self) -> None:
        """Reset engine to initial state."""
        self._balance = VirtualBalance(
            available=self._config.initial_balance
        )
        self._positions.clear()
        self._orders.clear()
        self._fills.clear()
        self._realized_pnl = 0.0
        self._total_fees_paid = 0.0
        
        logger.info(f"Reset paper trading engine for bot {self._bot_id}")
