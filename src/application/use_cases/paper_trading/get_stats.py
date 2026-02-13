"""Get paper trading statistics use case.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import logging
from typing import Dict

from src.application.paper_trading.paper_trading_engine import PaperTradingEngine

logger = logging.getLogger(__name__)


class GetPaperTradingStatsUseCase:
    """Get paper trading performance statistics.
    
    Returns:
    - Balance (available, reserved, total)
    - P&L (realized, unrealized, total)
    - Position metrics
    - Fee tracking
    - ROI calculation
    - Win rate (if applicable)
    
    Examples:
        >>> use_case = GetPaperTradingStatsUseCase()
        >>> stats = await use_case.execute(engine=engine)
        >>> print(f"ROI: {stats['roi']:.2%}")
    """

    async def execute(self, engine: PaperTradingEngine) -> Dict:
        """Get performance statistics.
        
        Args:
            engine: Paper trading engine
        
        Returns:
            Statistics dictionary
        """
        # Get base performance summary
        summary = engine.get_performance_summary()
        
        # Add detailed balance breakdown
        summary["balance"] = {
            "available": engine.balance.available,
            "reserved": engine.balance.reserved,
            "total": engine.balance.total,
        }
        
        # Add position details
        positions = engine.positions
        summary["positions"] = [
            {
                "position_id": p.position_id,
                "market_id": p.market_id,
                "side": p.side.value,
                "size": p.size,
                "entry_price": p.entry_price,
                "current_price": p.current_price,
                "unrealized_pnl": p.unrealized_pnl,
                "value": p.value,
            }
            for p in positions
        ]
        
        # Add performance metrics
        summary["metrics"] = {
            "total_return_pct": summary["roi"] * 100,
            "total_pnl_usd": summary["total_pnl"],
            "fees_paid_usd": summary["total_fees"],
            "net_pnl_usd": summary["total_pnl"] - summary["total_fees"],
        }
        
        logger.debug(f"Retrieved paper trading stats: ROI {summary['roi']:.2%}")
        
        return summary
