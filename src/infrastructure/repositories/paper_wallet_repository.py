"""Paper wallet repository."""

import json
import logging
from decimal import Decimal
from uuid import UUID

from src.domain.entities.paper_position import PaperPosition
from src.domain.entities.paper_wallet import PaperWallet
from src.infrastructure.persistence.redis_client import RedisClient

logger = logging.getLogger(__name__)


class PaperWalletRepository:
    """Repository for paper wallet data.
    
    Stores paper wallet state in Redis for fast access.
    Separate from production wallet data.
    """

    def __init__(self, redis: RedisClient):
        """Initialize repository.
        
        Args:
            redis: Redis client
        """
        self.redis = redis
        self.wallet_key = "paper:wallet"
        self.positions_key = "paper:positions"

    async def save_wallet(self, wallet: PaperWallet) -> None:
        """Save paper wallet to Redis.
        
        Args:
            wallet: Paper wallet to save
        """
        data = {
            "wallet_id": str(wallet.wallet_id),
            "balance": str(wallet.balance),
            "initial_balance": str(wallet.initial_balance),
            "realized_pnl": str(wallet.realized_pnl),
            "unrealized_pnl": str(wallet.unrealized_pnl),
            "total_trades": wallet.total_trades,
            "winning_trades": wallet.winning_trades,
            "losing_trades": wallet.losing_trades,
            "created_at": wallet.created_at.isoformat(),
            "updated_at": wallet.updated_at.isoformat(),
        }
        
        await self.redis.set(self.wallet_key, json.dumps(data))
        logger.debug("Paper wallet saved", extra={"wallet_id": str(wallet.wallet_id)})

    async def get_wallet(self) -> PaperWallet | None:
        """Get paper wallet from Redis.
        
        Returns:
            Paper wallet or None if not found
        """
        data = await self.redis.get(self.wallet_key)
        
        if not data:
            return None
        
        wallet_data = json.loads(data)
        
        from datetime import datetime
        
        return PaperWallet(
            wallet_id=UUID(wallet_data["wallet_id"]),
            balance=Decimal(wallet_data["balance"]),
            initial_balance=Decimal(wallet_data["initial_balance"]),
            realized_pnl=Decimal(wallet_data["realized_pnl"]),
            unrealized_pnl=Decimal(wallet_data["unrealized_pnl"]),
            total_trades=wallet_data["total_trades"],
            winning_trades=wallet_data["winning_trades"],
            losing_trades=wallet_data["losing_trades"],
            created_at=datetime.fromisoformat(wallet_data["created_at"]),
            updated_at=datetime.fromisoformat(wallet_data["updated_at"]),
        )

    async def save_position(self, position: PaperPosition) -> None:
        """Save paper position to Redis.
        
        Args:
            position: Paper position to save
        """
        data = {
            "position_id": str(position.position_id),
            "wallet_id": str(position.wallet_id),
            "market_id": position.market_id,
            "side": position.side,
            "size": str(position.size),
            "entry_price": str(position.entry_price),
            "current_price": str(position.current_price) if position.current_price else None,
            "zone": position.zone,
            "opened_at": position.opened_at.isoformat(),
            "closed_at": position.closed_at.isoformat() if position.closed_at else None,
            "exit_price": str(position.exit_price) if position.exit_price else None,
            "realized_pnl": str(position.realized_pnl) if position.realized_pnl else None,
        }
        
        # Store in hash
        await self.redis.hset(
            self.positions_key,
            str(position.position_id),
            json.dumps(data),
        )
        
        logger.debug(
            "Paper position saved",
            extra={"position_id": str(position.position_id)},
        )

    async def get_positions(self, status: str | None = None) -> list[PaperPosition]:
        """Get paper positions from Redis.
        
        Args:
            status: Filter by status ('open' or 'closed')
            
        Returns:
            List of paper positions
        """
        positions_data = await self.redis.hgetall(self.positions_key)
        
        if not positions_data:
            return []
        
        from datetime import datetime
        
        positions = []
        for data_str in positions_data.values():
            pos_data = json.loads(data_str)
            
            position = PaperPosition(
                position_id=UUID(pos_data["position_id"]),
                wallet_id=UUID(pos_data["wallet_id"]),
                market_id=pos_data["market_id"],
                side=pos_data["side"],
                size=Decimal(pos_data["size"]),
                entry_price=Decimal(pos_data["entry_price"]),
                current_price=Decimal(pos_data["current_price"]) if pos_data["current_price"] else None,
                zone=pos_data["zone"],
                opened_at=datetime.fromisoformat(pos_data["opened_at"]),
                closed_at=datetime.fromisoformat(pos_data["closed_at"]) if pos_data["closed_at"] else None,
                exit_price=Decimal(pos_data["exit_price"]) if pos_data["exit_price"] else None,
                realized_pnl=Decimal(pos_data["realized_pnl"]) if pos_data["realized_pnl"] else None,
            )
            
            # Filter by status
            if status == "open" and not position.is_open:
                continue
            elif status == "closed" and position.is_open:
                continue
            
            positions.append(position)
        
        return positions
