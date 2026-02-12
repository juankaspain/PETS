"""Production wallet entity for real trading."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ProductionWallet:
    """Production wallet for real money trading.
    
    Immutable entity with hot/cold split:
    - Hot wallet: 10-20% capital, active trading
    - Cold wallet: 80-90% capital, security
    """

    wallet_id: UUID = field(default_factory=uuid4)
    address: str = field(default="")  # Ethereum address
    
    # Capital allocation
    total_balance: Decimal = field(default=Decimal("0"))
    hot_balance: Decimal = field(default=Decimal("0"))  # Active trading
    cold_balance: Decimal = field(default=Decimal("0"))  # Security
    
    # Hot wallet percentage (10-20%)
    hot_wallet_pct: Decimal = field(default=Decimal("0.15"))  # 15% default
    
    # Performance tracking
    realized_pnl: Decimal = field(default=Decimal("0"))
    unrealized_pnl: Decimal = field(default=Decimal("0"))
    total_trades: int = field(default=0)
    winning_trades: int = field(default=0)
    losing_trades: int = field(default=0)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate production wallet."""
        if self.total_balance < 0:
            raise ValueError("Total balance cannot be negative")
        
        if self.hot_balance < 0 or self.cold_balance < 0:
            raise ValueError("Hot/cold balance cannot be negative")
        
        if not (Decimal("0.10") <= self.hot_wallet_pct <= Decimal("0.20")):
            raise ValueError("Hot wallet percentage must be 10-20%")
        
        # Verify split
        if abs(self.hot_balance + self.cold_balance - self.total_balance) > Decimal("0.01"):
            raise ValueError("Hot + Cold must equal total balance")
    
    @property
    def total_value(self) -> Decimal:
        """Total portfolio value (balance + unrealized P&L)."""
        return self.total_balance + self.unrealized_pnl
    
    @property
    def available_hot_balance(self) -> Decimal:
        """Available hot wallet balance for trading."""
        return self.hot_balance
    
    @property
    def win_rate(self) -> Decimal:
        """Win rate percentage."""
        if self.total_trades == 0:
            return Decimal("0")
        return (Decimal(self.winning_trades) / Decimal(self.total_trades)) * Decimal("100")
    
    def needs_rebalance(self) -> bool:
        """Check if hot/cold rebalance needed.
        
        Returns:
            True if hot wallet is below 80% of target or above 120% of target
        """
        target_hot = self.total_balance * self.hot_wallet_pct
        
        if target_hot == 0:
            return False
        
        ratio = self.hot_balance / target_hot
        
        # Rebalance if hot wallet is <80% or >120% of target
        return ratio < Decimal("0.80") or ratio > Decimal("1.20")
    
    def calculate_rebalance(self) -> tuple[Decimal, str]:
        """Calculate rebalance amount.
        
        Returns:
            Tuple of (amount, direction)
            - amount: Absolute value to transfer
            - direction: 'hot_to_cold' or 'cold_to_hot'
        """
        target_hot = self.total_balance * self.hot_wallet_pct
        difference = self.hot_balance - target_hot
        
        if difference > 0:
            # Hot wallet has excess, transfer to cold
            return abs(difference), "hot_to_cold"
        else:
            # Hot wallet needs more, transfer from cold
            return abs(difference), "cold_to_hot"
    
    def deduct_hot(self, amount: Decimal) -> "ProductionWallet":
        """Deduct from hot wallet (e.g., for order placement).
        
        Args:
            amount: Amount to deduct
            
        Returns:
            New ProductionWallet with updated balance
        """
        new_hot = self.hot_balance - amount
        if new_hot < 0:
            raise ValueError(f"Insufficient hot balance: {self.hot_balance} < {amount}")
        
        return ProductionWallet(
            wallet_id=self.wallet_id,
            address=self.address,
            total_balance=self.total_balance - amount,
            hot_balance=new_hot,
            cold_balance=self.cold_balance,
            hot_wallet_pct=self.hot_wallet_pct,
            realized_pnl=self.realized_pnl,
            unrealized_pnl=self.unrealized_pnl,
            total_trades=self.total_trades,
            winning_trades=self.winning_trades,
            losing_trades=self.losing_trades,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )
    
    def add_hot(self, amount: Decimal) -> "ProductionWallet":
        """Add to hot wallet (e.g., from position close).
        
        Args:
            amount: Amount to add
            
        Returns:
            New ProductionWallet with updated balance
        """
        return ProductionWallet(
            wallet_id=self.wallet_id,
            address=self.address,
            total_balance=self.total_balance + amount,
            hot_balance=self.hot_balance + amount,
            cold_balance=self.cold_balance,
            hot_wallet_pct=self.hot_wallet_pct,
            realized_pnl=self.realized_pnl,
            unrealized_pnl=self.unrealized_pnl,
            total_trades=self.total_trades,
            winning_trades=self.winning_trades,
            losing_trades=self.losing_trades,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )
    
    def transfer_to_cold(self, amount: Decimal) -> "ProductionWallet":
        """Transfer from hot to cold wallet.
        
        Args:
            amount: Amount to transfer
            
        Returns:
            New ProductionWallet with updated balances
        """
        new_hot = self.hot_balance - amount
        if new_hot < 0:
            raise ValueError(f"Insufficient hot balance for transfer: {self.hot_balance} < {amount}")
        
        return ProductionWallet(
            wallet_id=self.wallet_id,
            address=self.address,
            total_balance=self.total_balance,
            hot_balance=new_hot,
            cold_balance=self.cold_balance + amount,
            hot_wallet_pct=self.hot_wallet_pct,
            realized_pnl=self.realized_pnl,
            unrealized_pnl=self.unrealized_pnl,
            total_trades=self.total_trades,
            winning_trades=self.winning_trades,
            losing_trades=self.losing_trades,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )
    
    def transfer_to_hot(self, amount: Decimal) -> "ProductionWallet":
        """Transfer from cold to hot wallet.
        
        Args:
            amount: Amount to transfer
            
        Returns:
            New ProductionWallet with updated balances
        """
        new_cold = self.cold_balance - amount
        if new_cold < 0:
            raise ValueError(f"Insufficient cold balance for transfer: {self.cold_balance} < {amount}")
        
        return ProductionWallet(
            wallet_id=self.wallet_id,
            address=self.address,
            total_balance=self.total_balance,
            hot_balance=self.hot_balance + amount,
            cold_balance=new_cold,
            hot_wallet_pct=self.hot_wallet_pct,
            realized_pnl=self.realized_pnl,
            unrealized_pnl=self.unrealized_pnl,
            total_trades=self.total_trades,
            winning_trades=self.winning_trades,
            losing_trades=self.losing_trades,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )
