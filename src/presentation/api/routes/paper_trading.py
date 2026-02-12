"""Paper trading routes."""

import logging
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from src.application.bots.bot8_volatility_skew import Bot8VolatilitySkew
from src.application.use_cases.backtest_strategy import BacktestStrategyUseCase
from src.infrastructure.paper_trading.backtest_engine import BacktestEngine
from src.infrastructure.paper_trading.market_simulator import MarketSimulator
from src.infrastructure.paper_trading.paper_wallet import PaperWallet
from src.infrastructure.paper_trading.simulated_execution import SimulatedExecution
from src.presentation.api.schemas.paper_trading import (
    BacktestRequest,
    BacktestResponse,
    PaperTradeResponse,
    PaperTradingStart,
    PaperTradingStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Global state (in production, use Redis or database)
_paper_sessions = {}
_backtest_results = {}


@router.post("/start", response_model=dict, status_code=201)
async def start_paper_trading(
    request: PaperTradingStart,
):
    """Start paper trading session.

    Args:
        request: Paper trading start request

    Returns:
        Session ID
    """
    logger.info(
        "Starting paper trading session",
        extra={"initial_balance": float(request.initial_balance)},
    )

    # Create paper wallet
    paper_wallet = PaperWallet(initial_balance=request.initial_balance)

    # Create execution engine
    execution_engine = SimulatedExecution(paper_wallet)

    # Create strategy
    strategy = Bot8VolatilitySkew(config=request.strategy_config)

    # Generate session ID
    session_id = str(uuid4())

    # Store session
    _paper_sessions[session_id] = {
        "session_id": session_id,
        "paper_wallet": paper_wallet,
        "execution_engine": execution_engine,
        "strategy": strategy,
        "active": True,
        "started_at": datetime.utcnow(),
    }

    return {"session_id": session_id}


@router.get("/status", response_model=PaperTradingStatus)
async def get_paper_trading_status(
    session_id: str,
):
    """Get paper trading session status.

    Args:
        session_id: Session ID

    Returns:
        Paper trading status
    """
    session = _paper_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    paper_wallet = session["paper_wallet"]
    stats = paper_wallet.get_statistics({})  # Empty prices for closed positions

    return PaperTradingStatus(
        session_id=session_id,
        active=session["active"],
        initial_balance=Decimal(str(stats["initial_balance"])),
        current_balance=Decimal(str(stats["current_balance"])),
        total_value=Decimal(str(stats["total_value"])),
        total_pnl=Decimal(str(stats["total_pnl"])),
        return_pct=Decimal(str(stats["return_pct"])),
        open_positions=stats["open_positions"],
        total_trades=stats["total_trades"],
        winning_trades=stats["winning_trades"],
        losing_trades=stats["losing_trades"],
        win_rate=Decimal(str(stats["win_rate"])),
        started_at=session["started_at"],
    )


@router.get("/trades", response_model=list[PaperTradeResponse])
async def list_paper_trades(
    session_id: str,
    limit: int = 100,
):
    """List paper trades.

    Args:
        session_id: Session ID
        limit: Maximum results

    Returns:
        List of paper trades
    """
    session = _paper_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    paper_wallet = session["paper_wallet"]
    positions = paper_wallet.get_closed_positions()[:limit]

    return [
        PaperTradeResponse(
            position_id=str(pos.position_id),
            market_id=pos.market_id,
            side=pos.side,
            size=pos.size,
            entry_price=pos.entry_price,
            exit_price=pos.exit_price,
            realized_pnl=pos.realized_pnl,
            opened_at=pos.opened_at,
            closed_at=pos.closed_at,
        )
        for pos in positions
    ]


@router.post("/backtest", response_model=dict, status_code=201)
async def run_backtest(
    request: BacktestRequest,
):
    """Run backtest.

    Args:
        request: Backtest request

    Returns:
        Backtest ID
    """
    logger.info(
        "Starting backtest",
        extra={
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
        },
    )

    # Generate synthetic historical data (in production, fetch from DB)
    simulator = MarketSimulator(seed=42)
    historical_data = []

    # Create Bot 8 opportunity scenarios
    for i in range(10):  # 10 opportunities
        market_id = f"market_{i}"
        snapshots = simulator.simulate_bot8_opportunity(
            market_id=market_id,
            entry_type="cheap_yes" if i % 2 == 0 else "expensive_no",
        )

        for snapshot in snapshots:
            historical_data.append({
                "timestamp": snapshot.timestamp,
                "market_id": snapshot.market_id,
                "question": f"Test market {i}",
                "outcomes": ["YES", "NO"],
                "liquidity": float(snapshot.liquidity),
                "yes_price": float(snapshot.yes_price),
                "no_price": float(snapshot.no_price),
            })

    # Sort by timestamp
    historical_data.sort(key=lambda x: x["timestamp"])

    # Run backtest
    use_case = BacktestStrategyUseCase()
    result = await use_case.execute(
        strategy_config=request.strategy_config,
        historical_data=historical_data,
        start_date=request.start_date,
        end_date=request.end_date,
        initial_balance=request.initial_balance,
    )

    # Store result
    backtest_id = str(uuid4())
    _backtest_results[backtest_id] = result

    return {"backtest_id": backtest_id}


@router.get("/backtest/{backtest_id}", response_model=BacktestResponse)
async def get_backtest_result(
    backtest_id: str,
):
    """Get backtest result.

    Args:
        backtest_id: Backtest ID

    Returns:
        Backtest result
    """
    result = _backtest_results.get(backtest_id)
    if not result:
        raise HTTPException(status_code=404, detail="Backtest not found")

    return BacktestResponse(
        backtest_id=backtest_id,
        strategy_name=result.strategy_name,
        start_date=result.start_date,
        end_date=result.end_date,
        initial_balance=result.initial_balance,
        final_balance=result.final_balance,
        total_pnl=result.total_pnl,
        return_pct=result.return_pct,
        total_trades=result.total_trades,
        winning_trades=result.winning_trades,
        losing_trades=result.losing_trades,
        win_rate=result.win_rate,
        profit_factor=result.profit_factor,
        sharpe_ratio=result.sharpe_ratio,
        max_drawdown_pct=result.max_drawdown_pct,
        trades_count=len(result.trades),
    )
