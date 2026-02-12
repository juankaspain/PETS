"""Paper trading routes."""

import logging
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, HTTPException

from src.application.use_cases.run_paper_trading import RunPaperTradingUseCase
from src.infrastructure.paper_trading.backtesting.data_loader import (
    HistoricalDataLoader,
)
from src.infrastructure.paper_trading.backtesting.engine import BacktestEngine
from src.application.bots.bot8_volatility_skew import Bot8VolatilitySkew
from src.presentation.api.schemas.paper_trading import (
    BacktestRequest,
    BacktestResponse,
    PaperTradingStartRequest,
    PaperTradingStatusResponse,
    WalletStateResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Global use case instance
paper_trading_use_case = RunPaperTradingUseCase()


@router.post("/start", response_model=dict, status_code=201)
async def start_paper_trading(
    request: PaperTradingStartRequest,
):
    """Start paper trading session.

    Args:
        request: Start request

    Returns:
        Session info
    """
    logger.info(
        "Starting paper trading",
        extra={"initial_balance": float(request.initial_balance)},
    )

    session_id = f"session_{datetime.utcnow().timestamp()}"

    try:
        session = await paper_trading_use_case.start_session(
            session_id=session_id,
            initial_balance=request.initial_balance,
            bot_config=request.bot_config,
        )

        return {
            "session_id": session_id,
            "started_at": session.started_at.isoformat(),
            "initial_balance": float(session.initial_balance),
        }
    except Exception as e:
        logger.error(f"Failed to start paper trading: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop/{session_id}", status_code=204)
async def stop_paper_trading(
    session_id: str,
):
    """Stop paper trading session.

    Args:
        session_id: Session ID
    """
    logger.info("Stopping paper trading", extra={"session_id": session_id})

    try:
        await paper_trading_use_case.stop_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to stop paper trading: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{session_id}", response_model=PaperTradingStatusResponse)
async def get_status(
    session_id: str,
):
    """Get paper trading session status.

    Args:
        session_id: Session ID

    Returns:
        Session status
    """
    session = paper_trading_use_case.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    stats = session.wallet.get_statistics()

    return PaperTradingStatusResponse(
        session_id=session_id,
        is_running=session.is_running,
        started_at=session.started_at,
        initial_balance=session.initial_balance,
        current_balance=session.wallet.balance,
        total_value=session.wallet.total_value,
        total_pnl=session.wallet.total_pnl,
        open_positions=len(session.wallet.open_positions),
        closed_positions=len(session.wallet.closed_positions),
        total_trades=stats["total_trades"],
        win_rate=Decimal(str(stats["win_rate"])),
    )


@router.get("/wallet/{session_id}", response_model=WalletStateResponse)
async def get_wallet_state(
    session_id: str,
):
    """Get wallet state.

    Args:
        session_id: Session ID

    Returns:
        Wallet state
    """
    session = paper_trading_use_case.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    open_positions = [
        {
            "position_id": str(pos.position_id),
            "market_id": pos.market_id,
            "side": pos.side,
            "size": float(pos.size),
            "entry_price": float(pos.entry_price),
            "opened_at": pos.opened_at.isoformat(),
        }
        for pos in session.wallet.open_positions
    ]

    closed_positions = [
        {
            "position_id": str(pos.position_id),
            "market_id": pos.market_id,
            "side": pos.side,
            "size": float(pos.size),
            "entry_price": float(pos.entry_price),
            "exit_price": float(pos.exit_price) if pos.exit_price else None,
            "realized_pnl": float(pos.realized_pnl) if pos.realized_pnl else None,
            "opened_at": pos.opened_at.isoformat(),
            "closed_at": pos.closed_at.isoformat() if pos.closed_at else None,
        }
        for pos in session.wallet.closed_positions
    ]

    return WalletStateResponse(
        balance=session.wallet.balance,
        total_value=session.wallet.total_value,
        total_pnl=session.wallet.total_pnl,
        open_positions=open_positions,
        closed_positions=closed_positions,
    )


@router.post("/backtest", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
):
    """Run backtest.

    Args:
        request: Backtest request

    Returns:
        Backtest results
    """
    logger.info(
        "Running backtest",
        extra={
            "market_id": request.market_id,
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
        },
    )

    try:
        # Create bot and engine
        bot = Bot8VolatilitySkew(config=request.bot_config or {})
        engine = BacktestEngine(strategy=bot, initial_balance=request.initial_balance)

        # Load data
        data_loader = HistoricalDataLoader()
        price_data = data_loader.load_price_data(
            market_id=request.market_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        # Run backtest
        result = engine.run(
            market_id=request.market_id,
            start_date=request.start_date,
            end_date=request.end_date,
            price_data=price_data,
        )

        return BacktestResponse(
            start_date=result.start_date,
            end_date=result.end_date,
            initial_balance=result.initial_balance,
            final_balance=result.final_balance,
            total_return=result.total_return,
            total_return_pct=result.total_return_pct,
            total_trades=result.total_trades,
            winning_trades=result.winning_trades,
            losing_trades=result.losing_trades,
            win_rate=result.win_rate,
            profit_factor=result.profit_factor,
            sharpe_ratio=result.sharpe_ratio,
            max_drawdown=result.max_drawdown,
            avg_win=result.avg_win,
            avg_loss=result.avg_loss,
        )
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
