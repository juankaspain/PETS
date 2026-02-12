"""Paper position entity for simulated trading."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class PaperPosition:
    """Paper position for simulated trading.
    
    Immutable entity representing a simulated trading position.
    No real blockchain transactions.
    """

    position_id: UUID = field(default_factory=uuid4)
    wallet_id: UUID = field(default_factory=uuid4)
    market_id: str = field(default="")
    side: str = field(default="BUY")  # BUY or SELL
    size: Decimal = field(default=Decimal("0"))
    entry_price: Decimal = field(default=Decimal("0"))
    current_price: Decimal | None = field(default=None)
    zone: int = field(default=1)
    opened_at: datetime = field(default_factory=datetime.utcnow)
    closed_at: datetime | None = field(default=None)
    exit_price: Decimal | None = field(default=None)
    realized_pnl: Decimal | None = field(default=None)

    def __post_init__(self):
        """Validate paper position."""
        if self.size <= 0:
            raise ValueError("Position size must be positive")
        
        if self.entry_price <= 0 or self.entry_price >= 1:
            raise ValueError("Entry price must be between 0 and 1")
        
        if self.side not in ["BUY", "SELL"]:
            raise ValueError(f"Invalid side: {self.side}")
        
        if self.zone < 1 or self.zone > 5:
            raise ValueError(f"Zone must be 1-5, got {self.zone}")
    
    @property
    def is_open(self) -> bool:
        """Check if position is open."""
        return self.closed_at is None
    
    @property
    def unrealized_pnl(self) -> Decimal | None:
        """Calculate unrealized P&L.
        
        Returns:
            Unrealized P&L or None if position closed or no current price
        """
        if not self.is_open or self.current_price is None:
            return None
        
        if self.side == "BUY":
            return (self.current_price - self.entry_price) * self.size
        else:
            return (self.entry_price - self.current_price) * self.size
    
    @property
    def cost_basis(self) -> Decimal:
        """Cost basis (entry price * size)."""
        return self.entry_price * self.size
    
    def update_price(self, current_price: Decimal) -> "PaperPosition":
        """Update current price for P&L calculation.
        
        Args:
            current_price: Current market price
            
        Returns:
            New PaperPosition with updated price
        """
        if not self.is_open:
            raise ValueError("Cannot update price of closed position")
        
        return PaperPosition(
            position_id=self.position_id,
            wallet_id=self.wallet_id,
            market_id=self.market_id,
            side=self.side,
            size=self.size,
            entry_price=self.entry_price,
            current_price=current_price,
            zone=self.zone,
            opened_at=self.opened_at,
            closed_at=self.closed_at,
            exit_price=self.exit_price,
            realized_pnl=self.realized_pnl,
        )
    
    def close(self, exit_price: Decimal) -> "PaperPosition":
        """Close position and calculate realized P&L.
        
        Args:
            exit_price: Exit price
            
        Returns:
            New PaperPosition with closed status
        """
        if not self.is_open:
            raise ValueError("Position already closed")
        
        if exit_price <= 0 or exit_price >= 1:
            raise ValueError("Exit price must be between 0 and 1")
        
        # Calculate realized P&L
        if self.side == "BUY":
            pnl = (exit_price - self.entry_price) * self.size
        else:
            pnl = (self.entry_price - exit_price) * self.size
        
        # Apply maker rebate (20%)
        maker_rebate = self.size * Decimal("0.002")  # 0.2% = 20 basis points
        pnl += maker_rebate * 2  # Entry + exit both get rebate
        
        return PaperPosition(
            position_id=self.position_id,
            wallet_id=self.wallet_id,
            market_id=self.market_id,
            side=self.side,
            size=self.size,
            entry_price=self.entry_price,
            current_price=exit_price,
            zone=self.zone,
            opened_at=self.opened_at,
            closed_at=datetime.utcnow(),
            exit_price=exit_price,
            realized_pnl=pnl,
        )
