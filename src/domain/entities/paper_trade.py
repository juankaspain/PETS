"""Paper trade entity for simulated trading."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class PaperTrade:
    """Paper trade for simulated execution.
    
    Immutable entity representing a simulated trade.
    Records when orders are filled in paper trading.
    """

    trade_id: UUID = field(default_factory=uuid4)
    position_id: UUID = field(default_factory=uuid4)
    wallet_id: UUID = field(default_factory=uuid4)
    market_id: str = field(default="")
    side: str = field(default="BUY")  # BUY or SELL
    size: Decimal = field(default=Decimal("0"))
    price: Decimal = field(default=Decimal("0"))
    executed_at: datetime = field(default_factory=datetime.utcnow)
    
    # Simulated execution details
    is_maker: bool = field(default=True)  # Always maker for post-only
    fee_rate: Decimal = field(default=Decimal("-0.002"))  # -0.2% maker rebate
    fee_amount: Decimal = field(default=Decimal("0"))
    net_amount: Decimal = field(default=Decimal("0"))

    def __post_init__(self):
        """Validate paper trade."""
        if self.size <= 0:
            raise ValueError("Trade size must be positive")
        
        if self.price <= 0 or self.price >= 1:
            raise ValueError("Trade price must be between 0 and 1")
        
        if self.side not in ["BUY", "SELL"]:
            raise ValueError(f"Invalid side: {self.side}")
        
        # Calculate fee and net amount
        gross_amount = self.size * self.price
        fee = gross_amount * self.fee_rate
        
        # Update mutable fields (hack for frozen dataclass with calculated fields)
        object.__setattr__(self, "fee_amount", fee)
        object.__setattr__(self, "net_amount", gross_amount - fee)
    
    @property
    def cost(self) -> Decimal:
        """Total cost including fees (negative fee = rebate)."""
        return self.size * self.price - self.fee_amount
