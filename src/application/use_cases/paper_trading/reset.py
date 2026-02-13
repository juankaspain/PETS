"""Reset paper trading engine use case.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import logging
from typing import Dict

from src.application.paper_trading.paper_trading_engine import PaperTradingEngine

logger = logging.getLogger(__name__)


class ResetPaperTradingUseCase:
    """Reset paper trading engine to initial state.
    
    Clears:
    - Virtual balance (reset to initial)
    - All positions
    - Order history
    - P&L tracking
    - Fee tracking
    
    Preserves:
    - Configuration
    - Bot ID
    
    Examples:
        >>> use_case = ResetPaperTradingUseCase()
        >>> await use_case.execute(engine=engine)
    """

    async def execute(self, engine: PaperTradingEngine) -> Dict[str, str]:
        """Reset paper trading engine.
        
        Args:
            engine: Engine to reset
        
        Returns:
            Status message
        """
        # Get bot_id before reset
        bot_id = engine._bot_id
        
        # Close any open positions before reset
        open_positions = len(engine.positions)
        
        logger.info(
            f"Resetting paper trading engine for bot {bot_id}, "
            f"{open_positions} open positions"
        )
        
        # Reset engine
        engine.reset()
        
        logger.info(f"Paper trading engine reset complete for bot {bot_id}")
        
        return {
            "status": "success",
            "message": f"Reset bot {bot_id}, cleared {open_positions} positions",
        }
