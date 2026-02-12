"""Backtesting routes."""

import logging
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter

from src.application.paper_trading.backtesting_engine import BacktestingEngine

logger = logging.getLogger(__name__)

router = APIRouter()

# Store backtest results in memory (TODO: use database)
backtest_results = {}


@router.post("/run")
async def run_backtest(
    start_date: str,
    end_date: str,
    initial_balance: float = 10000,
    parameters: dict | None = None,
):
    """Run backtest on historical data.
    
    Args:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        initial_balance: Starting balance
        parameters: Strategy parameters override
        
    Returns:
        Backtest result
    """
    logger.info(
        "Running backtest",
        extra={
            "start_date": start_date,
            "end_date": end_date,
            "initial_balance": initial_balance,
        },
    )
    
    engine = BacktestingEngine()
    
    result = await engine.run_backtest(
        start_date=datetime.fromisoformat(start_date),
        end_date=datetime.fromisoformat(end_date),
        initial_balance=Decimal(str(initial_balance)),
        parameters=parameters,
    )
    
    # Store result
    backtest_results[result.backtest_id] = result
    
    return {
        "backtest_id": result.backtest_id,
        "status": "complete",
        "initial_balance": float(result.initial_balance),
        "final_balance": float(result.final_balance),
        "total_return": float(result.total_return),
        "total_return_pct": float(result.total_return_pct),
        "total_trades": result.total_trades,
        "win_rate": float(result.win_rate),
        "profit_factor": float(result.profit_factor),
    }


@router.get("/results/{backtest_id}")
async def get_backtest_results(backtest_id: str):
    """Get backtest results.
    
    Args:
        backtest_id: Backtest ID
        
    Returns:
        Backtest result details
    """
    if backtest_id not in backtest_results:
        return {"error": "Backtest not found"}
    
    result = backtest_results[backtest_id]
    
    return {
        "backtest_id": result.backtest_id,
        "start_date": result.start_date.isoformat(),
        "end_date": result.end_date.isoformat(),
        "initial_balance": float(result.initial_balance),
        "final_balance": float(result.final_balance),
        "total_return": float(result.total_return),
        "total_return_pct": float(result.total_return_pct),
        "total_trades": result.total_trades,
        "winning_trades": result.winning_trades,
        "losing_trades": result.losing_trades,
        "win_rate": float(result.win_rate),
        "profit_factor": float(result.profit_factor),
        "sharpe_ratio": float(result.sharpe_ratio) if result.sharpe_ratio else None,
        "max_drawdown_pct": float(result.max_drawdown_pct),
        "avg_win": float(result.avg_win),
        "avg_loss": float(result.avg_loss),
        "avg_trade_duration_hours": result.avg_trade_duration_hours,
        "parameters": result.parameters,
    }


@router.get("/list")
async def list_backtests():
    """List all backtests.
    
    Returns:
        List of backtest summaries
    """
    return [
        {
            "backtest_id": result.backtest_id,
            "start_date": result.start_date.isoformat(),
            "end_date": result.end_date.isoformat(),
            "total_return_pct": float(result.total_return_pct),
            "win_rate": float(result.win_rate),
            "total_trades": result.total_trades,
        }
        for result in backtest_results.values()
    ]
