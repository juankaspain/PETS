"""Paper trading routes."""

import logging
from decimal import Decimal

from fastapi import APIRouter

from src.application.paper_trading.paper_wallet_service import PaperWalletService
from src.infrastructure.repositories.paper_wallet_repository import (
    PaperWalletRepository,
)
from src.presentation.api.dependencies import Redis

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/wallet")
async def get_paper_wallet(redis: Redis):
    """Get paper trading wallet.
    
    Args:
        redis: Redis client
        
    Returns:
        Paper wallet data
    """
    repo = PaperWalletRepository(redis)
    service = PaperWalletService()
    
    # Get or create wallet
    wallet = await repo.get_wallet()
    if not wallet:
        wallet = service.create_wallet()
        await repo.save_wallet(wallet)
    
    return {
        "wallet_id": str(wallet.wallet_id),
        "balance": float(wallet.balance),
        "initial_balance": float(wallet.initial_balance),
        "total_value": float(wallet.total_value),
        "realized_pnl": float(wallet.realized_pnl),
        "unrealized_pnl": float(wallet.unrealized_pnl),
        "total_return": float(wallet.total_return),
        "total_return_pct": float(wallet.total_return_pct),
        "total_trades": wallet.total_trades,
        "winning_trades": wallet.winning_trades,
        "losing_trades": wallet.losing_trades,
        "win_rate": float(wallet.win_rate),
    }


@router.post("/wallet/reset")
async def reset_paper_wallet(
    redis: Redis,
    initial_balance: float = 10000,
):
    """Reset paper trading wallet.
    
    Args:
        redis: Redis client
        initial_balance: Starting balance
        
    Returns:
        New paper wallet data
    """
    logger.info(
        "Resetting paper wallet",
        extra={"initial_balance": initial_balance},
    )
    
    repo = PaperWalletRepository(redis)
    service = PaperWalletService()
    
    # Create new wallet
    wallet = service.create_wallet(Decimal(str(initial_balance)))
    await repo.save_wallet(wallet)
    
    # Clear positions
    await redis.delete("paper:positions")
    
    return {
        "wallet_id": str(wallet.wallet_id),
        "balance": float(wallet.balance),
        "initial_balance": float(wallet.initial_balance),
        "message": "Paper wallet reset successfully",
    }


@router.get("/positions")
async def get_paper_positions(
    redis: Redis,
    status: str | None = None,
):
    """Get paper trading positions.
    
    Args:
        redis: Redis client
        status: Filter by status ('open' or 'closed')
        
    Returns:
        List of paper positions
    """
    repo = PaperWalletRepository(redis)
    positions = await repo.get_positions(status=status)
    
    return [
        {
            "position_id": str(pos.position_id),
            "market_id": pos.market_id,
            "side": pos.side,
            "size": float(pos.size),
            "entry_price": float(pos.entry_price),
            "current_price": float(pos.current_price) if pos.current_price else None,
            "zone": pos.zone,
            "opened_at": pos.opened_at.isoformat(),
            "closed_at": pos.closed_at.isoformat() if pos.closed_at else None,
            "exit_price": float(pos.exit_price) if pos.exit_price else None,
            "unrealized_pnl": float(pos.unrealized_pnl) if pos.unrealized_pnl else None,
            "realized_pnl": float(pos.realized_pnl) if pos.realized_pnl else None,
            "is_open": pos.is_open,
        }
        for pos in positions
    ]


@router.get("/metrics")
async def get_paper_metrics(redis: Redis):
    """Get paper trading metrics.
    
    Args:
        redis: Redis client
        
    Returns:
        Paper trading performance metrics
    """
    repo = PaperWalletRepository(redis)
    
    wallet = await repo.get_wallet()
    if not wallet:
        return {
            "total_value": 0,
            "total_return": 0,
            "total_return_pct": 0,
            "total_trades": 0,
            "win_rate": 0,
            "profit_factor": 0,
        }
    
    positions = await repo.get_positions(status="closed")
    
    # Calculate metrics
    total_wins = sum(pos.realized_pnl for pos in positions if pos.realized_pnl and pos.realized_pnl > 0)
    total_losses = sum(abs(pos.realized_pnl) for pos in positions if pos.realized_pnl and pos.realized_pnl < 0)
    
    profit_factor = float(total_wins / total_losses) if total_losses > 0 else 0
    
    return {
        "total_value": float(wallet.total_value),
        "total_return": float(wallet.total_return),
        "total_return_pct": float(wallet.total_return_pct),
        "total_trades": wallet.total_trades,
        "winning_trades": wallet.winning_trades,
        "losing_trades": wallet.losing_trades,
        "win_rate": float(wallet.win_rate),
        "profit_factor": profit_factor,
        "avg_win": float(total_wins / wallet.winning_trades) if wallet.winning_trades > 0 else 0,
        "avg_loss": float(total_losses / wallet.losing_trades) if wallet.losing_trades > 0 else 0,
    }
