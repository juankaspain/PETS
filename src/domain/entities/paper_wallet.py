"""Paper wallet entity for simulated trading."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class PaperWallet:
    """Paper wallet for simulated trading.
    
    Immutable entity representing a virtual wallet for paper trading.
    No real blockchain transactions, all simulated.
    """

    wallet_id: UUID = field(default_factory=uuid4)
    balance: Decimal = field(default=Decimal("10000"))  # Virtual $10K
    initial_balance: Decimal = field(default=Decimal("10000"))
    realized_pnl: Decimal = field(default=Decimal("0"))
    unrealized_pnl: Decimal = field(default=Decimal("0"))
    total_trades: int = field(default=0)
    winning_trades: int = field(default=0)
    losing_trades: int = field(default=0)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate paper wallet."""
        if self.balance < 0:
            raise ValueError("Paper wallet balance cannot be negative")
        
        if self.initial_balance <= 0:
            raise ValueError("Initial balance must be positive")
    
    @property
    def total_value(self) -> Decimal:
        """Total portfolio value (balance + unrealized P&L)."""
        return self.balance + self.unrealized_pnl
    
    @property
    def total_return(self) -> Decimal:
        """Total return (realized + unrealized P&L)."""
        return self.realized_pnl + self.unrealized_pnl
    
    @property
    def total_return_pct(self) -> Decimal:
        """Total return percentage."""
        if self.initial_balance == 0:
            return Decimal("0")
        return (self.total_return / self.initial_balance) * Decimal("100")
    
    @property
    def win_rate(self) -> Decimal:
        """Win rate percentage."""
        if self.total_trades == 0:
            return Decimal("0")
        return (Decimal(self.winning_trades) / Decimal(self.total_trades)) * Decimal("100")
    
    def deduct(self, amount: Decimal) -> "PaperWallet":
        """Deduct amount from balance (e.g., for order placement).
        
        Args:
            amount: Amount to deduct
            
        Returns:
            New PaperWallet with updated balance
        """
        new_balance = self.balance - amount
        if new_balance < 0:
            raise ValueError(f"Insufficient balance: {self.balance} < {amount}")
        
        return PaperWallet(
            wallet_id=self.wallet_id,
            balance=new_balance,
            initial_balance=self.initial_balance,
            realized_pnl=self.realized_pnl,
            unrealized_pnl=self.unrealized_pnl,
            total_trades=self.total_trades,
            winning_trades=self.winning_trades,
            losing_trades=self.losing_trades,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )
    
    def add(self, amount: Decimal) -> "PaperWallet":
        """Add amount to balance (e.g., from position close).
        
        Args:
            amount: Amount to add
            
        Returns:
            New PaperWallet with updated balance
        """
        return PaperWallet(
            wallet_id=self.wallet_id,
            balance=self.balance + amount,
            initial_balance=self.initial_balance,
            realized_pnl=self.realized_pnl,
            unrealized_pnl=self.unrealized_pnl,
            total_trades=self.total_trades,
            winning_trades=self.winning_trades,
            losing_trades=self.losing_trades,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )
    
    def record_trade(self, pnl: Decimal) -> "PaperWallet":
        """Record closed trade and update stats.
        
        Args:
            pnl: Realized P&L from trade
            
        Returns:
            New PaperWallet with updated stats
        """
        new_realized_pnl = self.realized_pnl + pnl
        new_total_trades = self.total_trades + 1
        new_winning_trades = self.winning_trades + (1 if pnl > 0 else 0)
        new_losing_trades = self.losing_trades + (1 if pnl < 0 else 0)
        
        return PaperWallet(
            wallet_id=self.wallet_id,
            balance=self.balance,
            initial_balance=self.initial_balance,
            realized_pnl=new_realized_pnl,
            unrealized_pnl=self.unrealized_pnl,
            total_trades=new_total_trades,
            winning_trades=new_winning_trades,
            losing_trades=new_losing_trades,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )
