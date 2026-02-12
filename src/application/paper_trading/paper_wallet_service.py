"""Paper wallet service for simulated trading."""

import logging
from decimal import Decimal
from uuid import UUID

from src.domain.entities.paper_position import PaperPosition
from src.domain.entities.paper_trade import PaperTrade
from src.domain.entities.paper_wallet import PaperWallet

logger = logging.getLogger(__name__)


class PaperWalletService:
    """Service for managing paper trading wallet.
    
    Handles:
    - Wallet creation and reset
    - Order placement (deduct balance)
    - Order fills (create position)
    - Position closes (add balance, record P&L)
    - Stats tracking
    """

    def __init__(self):
        """Initialize paper wallet service."""
        pass

    def create_wallet(self, initial_balance: Decimal = Decimal("10000")) -> PaperWallet:
        """Create new paper wallet.
        
        Args:
            initial_balance: Starting balance
            
        Returns:
            New paper wallet
        """
        logger.info(
            "Creating paper wallet",
            extra={"initial_balance": float(initial_balance)},
        )
        
        return PaperWallet(
            balance=initial_balance,
            initial_balance=initial_balance,
        )

    def place_order(
        self,
        wallet: PaperWallet,
        market_id: str,
        side: str,
        size: Decimal,
        price: Decimal,
    ) -> tuple[PaperWallet, UUID]:
        """Place simulated order (deduct balance).
        
        Args:
            wallet: Paper wallet
            market_id: Market ID
            side: Order side (BUY or SELL)
            size: Order size
            price: Limit price
            
        Returns:
            Updated wallet and order ID
        """
        # Calculate cost (for BUY orders)
        if side == "BUY":
            cost = size * price
            new_wallet = wallet.deduct(cost)
        else:
            # For SELL, we need the position (not implemented here)
            new_wallet = wallet
        
        # Generate order ID
        from uuid import uuid4
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
        
        return new_wallet, order_id

    def fill_order(
        self,
        wallet: PaperWallet,
        order_id: UUID,
        market_id: str,
        side: str,
        size: Decimal,
        fill_price: Decimal,
        zone: int,
    ) -> tuple[PaperWallet, PaperPosition, PaperTrade]:
        """Simulate order fill and create position.
        
        Args:
            wallet: Paper wallet
            order_id: Order ID
            market_id: Market ID
            side: Order side
            size: Fill size
            fill_price: Fill price
            zone: Risk zone
            
        Returns:
            Updated wallet, new position, trade record
        """
        # Create position
        position = PaperPosition(
            wallet_id=wallet.wallet_id,
            market_id=market_id,
            side=side,
            size=size,
            entry_price=fill_price,
            zone=zone,
        )
        
        # Create trade record
        trade = PaperTrade(
            position_id=position.position_id,
            wallet_id=wallet.wallet_id,
            market_id=market_id,
            side=side,
            size=size,
            price=fill_price,
        )
        
        logger.info(
            "Paper order filled",
            extra={
                "order_id": str(order_id),
                "position_id": str(position.position_id),
                "fill_price": float(fill_price),
                "fee_amount": float(trade.fee_amount),
            },
        )
        
        return wallet, position, trade

    def close_position(
        self,
        wallet: PaperWallet,
        position: PaperPosition,
        exit_price: Decimal,
    ) -> tuple[PaperWallet, PaperPosition, PaperTrade]:
        """Close position and update wallet.
        
        Args:
            wallet: Paper wallet
            position: Position to close
            exit_price: Exit price
            
        Returns:
            Updated wallet, closed position, exit trade
        """
        # Close position
        closed_position = position.close(exit_price)
        
        # Add proceeds to wallet
        if position.side == "BUY":
            proceeds = position.size * exit_price
        else:
            # For SELL, return collateral + P&L
            proceeds = position.cost_basis + closed_position.realized_pnl
        
        new_wallet = wallet.add(proceeds)
        
        # Record trade stats
        new_wallet = new_wallet.record_trade(closed_position.realized_pnl)
        
        # Create exit trade record
        exit_trade = PaperTrade(
            position_id=position.position_id,
            wallet_id=wallet.wallet_id,
            market_id=position.market_id,
            side="SELL" if position.side == "BUY" else "BUY",
            size=position.size,
            price=exit_price,
        )
        
        logger.info(
            "Paper position closed",
            extra={
                "position_id": str(position.position_id),
                "exit_price": float(exit_price),
                "realized_pnl": float(closed_position.realized_pnl),
                "new_balance": float(new_wallet.balance),
            },
        )
        
        return new_wallet, closed_position, exit_trade
