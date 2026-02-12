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


@dataclass
class PaperTrade:
    """Paper trade record."""

    trade_id: UUID
    position_id: UUID
    market_id: str
    side: str
    size: Decimal
    price: Decimal
    fee: Decimal  # Negative for maker rebate
    timestamp: datetime


class PaperWallet:
    """Paper wallet for simulated trading without real money.

    Tracks virtual balance, positions, and trades.
    Simulates maker rebate (20%) without blockchain transactions.
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
            extra={
                "initial_balance": float(initial_balance),
                "timestamp": self.created_at.isoformat(),
            },
        )

    @property
    def total_value(self) -> Decimal:
        """Calculate total portfolio value (cash + positions).

        Returns:
            Total value
        """
        position_value = sum(
            pos.size * pos.entry_price
            for pos in self.positions.values()
            if pos.closed_at is None
        )
        return self.balance + position_value

    @property
    def total_pnl(self) -> Decimal:
        """Calculate total realized P&L.

        Returns:
            Total P&L
        """
        return sum(
            pos.realized_pnl
            for pos in self.positions.values()
            if pos.realized_pnl is not None
        )

    @property
    def open_positions(self) -> List[PaperPosition]:
        """Get open positions.

        Returns:
            List of open positions
        """
        return [
            pos for pos in self.positions.values() if pos.closed_at is None
        ]

    @property
    def closed_positions(self) -> List[PaperPosition]:
        """Get closed positions.

        Returns:
            List of closed positions
        """
        return [
            pos for pos in self.positions.values() if pos.closed_at is not None
        ]

    def open_position(
        self,
        market_id: str,
        side: str,
        size: Decimal,
        price: Decimal,
    ) -> PaperPosition:
        """Open a new position.

        Args:
            market_id: Market ID
            side: BUY or SELL
            size: Position size
            price: Entry price

        Returns:
            Created position

        Raises:
            ValueError: If insufficient balance
        """
        # Calculate cost (including 20% maker rebate)
        cost = size * price
        maker_rebate = cost * Decimal("0.20")  # 20% rebate
        net_cost = cost - maker_rebate

        if net_cost > self.balance:
            raise ValueError(
                f"Insufficient balance: need ${net_cost}, have ${self.balance}"
            )

        # Create position
        position = PaperPosition(
            position_id=uuid4(),
            market_id=market_id,
            side=side,
            size=size,
            entry_price=price,
            opened_at=datetime.utcnow(),
        )

        # Update balance
        self.balance -= net_cost
        self.positions[position.position_id] = position

        # Record trade
        trade = PaperTrade(
            trade_id=uuid4(),
            position_id=position.position_id,
            market_id=market_id,
            side=side,
            size=size,
            price=price,
            fee=-maker_rebate,  # Negative = rebate
            timestamp=datetime.utcnow(),
        )
        self.trades.append(trade)

        logger.info(
            "Position opened",
            extra={
                "position_id": str(position.position_id),
                "market_id": market_id,
                "side": side,
                "size": float(size),
                "price": float(price),
                "net_cost": float(net_cost),
                "balance": float(self.balance),
            },
        )

        return position

    def close_position(
        self,
        position_id: UUID,
        exit_price: Decimal,
    ) -> PaperPosition:
        """Close an open position.

        Args:
            position_id: Position ID
            exit_price: Exit price

        Returns:
            Closed position

        Raises:
            ValueError: If position not found or already closed
        """
        position = self.positions.get(position_id)
        if not position:
            raise ValueError(f"Position {position_id} not found")
        if position.closed_at is not None:
            raise ValueError(f"Position {position_id} already closed")

        # Calculate P&L
        if position.side == "BUY":
            pnl = (exit_price - position.entry_price) * position.size
        else:
            pnl = (position.entry_price - exit_price) * position.size

        # Calculate maker rebate on exit
        exit_value = position.size * exit_price
        maker_rebate = exit_value * Decimal("0.20")
        pnl += maker_rebate  # Add rebate to P&L

        # Update position
        position.closed_at = datetime.utcnow()
        position.exit_price = exit_price
        position.realized_pnl = pnl

        # Update balance
        self.balance += exit_value + maker_rebate

        # Record trade
        trade = PaperTrade(
            trade_id=uuid4(),
            position_id=position_id,
            market_id=position.market_id,
            side="SELL" if position.side == "BUY" else "BUY",
            size=position.size,
            price=exit_price,
            fee=-maker_rebate,
            timestamp=datetime.utcnow(),
        )
        self.trades.append(trade)

        logger.info(
            "Position closed",
            extra={
                "position_id": str(position_id),
                "entry_price": float(position.entry_price),
                "exit_price": float(exit_price),
                "realized_pnl": float(pnl),
                "balance": float(self.balance),
            },
        )

        return position

    def get_position(self, position_id: UUID) -> PaperPosition | None:
        """Get position by ID.

        Args:
            position_id: Position ID

        Returns:
            Position or None
        """
        return self.positions.get(position_id)

    def get_statistics(self) -> dict:
        """Get wallet statistics.

        Returns:
            Statistics dict
        """
        closed = self.closed_positions
        winning_trades = [p for p in closed if p.realized_pnl and p.realized_pnl > 0]
        losing_trades = [p for p in closed if p.realized_pnl and p.realized_pnl < 0]

        return {
            "initial_balance": float(self.initial_balance),
            "current_balance": float(self.balance),
            "total_value": float(self.total_value),
            "total_pnl": float(self.total_pnl),
            "return_pct": float(
                (self.total_value - self.initial_balance)
                / self.initial_balance
                * 100
            ),
            "open_positions": len(self.open_positions),
            "closed_positions": len(closed),
            "total_trades": len(self.trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": len(winning_trades) / len(closed) if closed else 0,
        }
