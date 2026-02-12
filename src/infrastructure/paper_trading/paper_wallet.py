"""Paper wallet for simulated trading."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


@dataclass
class PaperPosition:
    """Paper trading position."""

    position_id: UUID
    market_id: str
    side: str  # BUY or SELL
    size: Decimal
    entry_price: Decimal
    opened_at: datetime
    closed_at: datetime | None = None
    exit_price: Decimal | None = None
    realized_pnl: Decimal | None = None

    def calculate_unrealized_pnl(self, current_price: Decimal) -> Decimal:
        """Calculate unrealized P&L.

        Args:
            current_price: Current market price

        Returns:
            Unrealized P&L
        """
        if self.side == "BUY":
            return (current_price - self.entry_price) * self.size
        else:
            return (self.entry_price - current_price) * self.size

    def close(self, exit_price: Decimal) -> Decimal:
        """Close position and calculate realized P&L.

        Args:
            exit_price: Exit price

        Returns:
            Realized P&L
        """
        self.closed_at = datetime.utcnow()
        self.exit_price = exit_price
        self.realized_pnl = self.calculate_unrealized_pnl(exit_price)
        return self.realized_pnl


@dataclass
class PaperTrade:
    """Paper trading trade record."""

    trade_id: UUID
    position_id: UUID
    market_id: str
    side: str
    size: Decimal
    price: Decimal
    fee: Decimal  # Negative for maker rebate
    timestamp: datetime


class PaperWallet:
    """Paper wallet for simulated trading.

    Tracks virtual balance, positions, and trades without real money or blockchain transactions.
    """

    def __init__(self, initial_balance: Decimal = Decimal("10000")):
        """Initialize paper wallet.

        Args:
            initial_balance: Starting virtual balance (default $10K)
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions: Dict[UUID, PaperPosition] = {}
        self.trades: List[PaperTrade] = []
        self.created_at = datetime.utcnow()

        logger.info(
            "Paper wallet created",
            extra={"initial_balance": float(initial_balance)},
        )

    def get_balance(self) -> Decimal:
        """Get current balance.

        Returns:
            Current virtual balance
        """
        return self.balance

    def get_total_value(self, current_prices: Dict[str, Decimal]) -> Decimal:
        """Calculate total portfolio value.

        Args:
            current_prices: Dict of market_id -> current price

        Returns:
            Total value (balance + position value)
        """
        position_value = Decimal("0")

        for position in self.positions.values():
            if position.closed_at is None:
                current_price = current_prices.get(position.market_id)
                if current_price:
                    position_value += position.size * current_price

        return self.balance + position_value

    def get_total_pnl(self, current_prices: Dict[str, Decimal]) -> Decimal:
        """Calculate total P&L (realized + unrealized).

        Args:
            current_prices: Dict of market_id -> current price

        Returns:
            Total P&L
        """
        realized_pnl = sum(
            pos.realized_pnl
            for pos in self.positions.values()
            if pos.realized_pnl is not None
        )

        unrealized_pnl = Decimal("0")
        for position in self.positions.values():
            if position.closed_at is None:
                current_price = current_prices.get(position.market_id)
                if current_price:
                    unrealized_pnl += position.calculate_unrealized_pnl(current_price)

        return realized_pnl + unrealized_pnl

    def place_order(
        self,
        market_id: str,
        side: str,
        size: Decimal,
        price: Decimal,
    ) -> UUID:
        """Place simulated order.

        Args:
            market_id: Market ID
            side: Order side (BUY or SELL)
            size: Order size
            price: Limit price

        Returns:
            Order ID

        Raises:
            ValueError: If insufficient balance
        """
        # Check balance
        required = size * price
        if side == "BUY" and required > self.balance:
            raise ValueError(
                f"Insufficient balance: {self.balance} < {required}"
            )

        # Reserve balance for BUY orders
        if side == "BUY":
            self.balance -= required

        order_id = uuid4()

        logger.info(
            "Paper order placed",
            extra={
                "order_id": str(order_id),
                "market_id": market_id,
                "side": side,
                "size": float(size),
                "price": float(price),
            },
        )

        return order_id

    def fill_order(
        self,
        order_id: UUID,
        market_id: str,
        side: str,
        size: Decimal,
        fill_price: Decimal,
        maker_rebate_rate: Decimal = Decimal("0.002"),  # 20 bps
    ) -> UUID:
        """Simulate order fill.

        Args:
            order_id: Order ID
            market_id: Market ID
            side: Order side
            size: Fill size
            fill_price: Fill price
            maker_rebate_rate: Maker rebate rate (default 0.002 = 20 bps)

        Returns:
            Position ID
        """
        # Calculate fee (negative for maker rebate)
        fee = -(size * fill_price * maker_rebate_rate)

        # Create position
        position = PaperPosition(
            position_id=uuid4(),
            market_id=market_id,
            side=side,
            size=size,
            entry_price=fill_price,
            opened_at=datetime.utcnow(),
        )

        self.positions[position.position_id] = position

        # Create trade record
        trade = PaperTrade(
            trade_id=uuid4(),
            position_id=position.position_id,
            market_id=market_id,
            side=side,
            size=size,
            price=fill_price,
            fee=fee,
            timestamp=datetime.utcnow(),
        )

        self.trades.append(trade)

        # Add maker rebate to balance
        self.balance += abs(fee)

        logger.info(
            "Paper order filled",
            extra={
                "position_id": str(position.position_id),
                "fill_price": float(fill_price),
                "fee": float(fee),
            },
        )

        return position.position_id

    def close_position(
        self,
        position_id: UUID,
        exit_price: Decimal,
    ) -> Decimal:
        """Close position.

        Args:
            position_id: Position ID
            exit_price: Exit price

        Returns:
            Realized P&L

        Raises:
            ValueError: If position not found or already closed
        """
        position = self.positions.get(position_id)
        if not position:
            raise ValueError(f"Position {position_id} not found")

        if position.closed_at is not None:
            raise ValueError(f"Position {position_id} already closed")

        # Close position and calculate P&L
        realized_pnl = position.close(exit_price)

        # Update balance
        if position.side == "BUY":
            # Return position value at exit price
            self.balance += position.size * exit_price
        else:
            # Return collateral + profit/loss
            self.balance += position.size * position.entry_price + realized_pnl

        logger.info(
            "Paper position closed",
            extra={
                "position_id": str(position_id),
                "exit_price": float(exit_price),
                "realized_pnl": float(realized_pnl),
            },
        )

        return realized_pnl

    def get_open_positions(self) -> List[PaperPosition]:
        """Get all open positions.

        Returns:
            List of open positions
        """
        return [
            pos for pos in self.positions.values() if pos.closed_at is None
        ]

    def get_closed_positions(self) -> List[PaperPosition]:
        """Get all closed positions.

        Returns:
            List of closed positions
        """
        return [
            pos for pos in self.positions.values() if pos.closed_at is not None
        ]

    def get_statistics(self, current_prices: Dict[str, Decimal]) -> dict:
        """Get wallet statistics.

        Args:
            current_prices: Dict of market_id -> current price

        Returns:
            Statistics dict
        """
        closed = self.get_closed_positions()
        winning_trades = sum(1 for pos in closed if pos.realized_pnl and pos.realized_pnl > 0)
        losing_trades = sum(1 for pos in closed if pos.realized_pnl and pos.realized_pnl < 0)

        total_value = self.get_total_value(current_prices)
        total_pnl = self.get_total_pnl(current_prices)

        return {
            "initial_balance": float(self.initial_balance),
            "current_balance": float(self.balance),
            "total_value": float(total_value),
            "total_pnl": float(total_pnl),
            "return_pct": float(total_pnl / self.initial_balance * 100) if self.initial_balance > 0 else 0,
            "open_positions": len(self.get_open_positions()),
            "closed_positions": len(closed),
            "total_trades": len(closed),
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": winning_trades / len(closed) if closed else 0,
        }
