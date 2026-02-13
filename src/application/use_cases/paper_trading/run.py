"""Run paper trading session use case.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from src.application.paper_trading.paper_trading_engine import (
    PaperTradingConfig,
    PaperTradingEngine,
)
from src.domain.entities.order import OrderSide, OrderType

logger = logging.getLogger(__name__)


class RunPaperTradingUseCase:
    """Run paper trading session.
    
    Orchestrates complete paper trading workflow:
    1. Initialize engine with config
    2. Run bot strategy in virtual environment
    3. Process signals and place virtual orders
    4. Monitor positions and P&L
    5. Generate performance statistics
    
    Examples:
        >>> use_case = RunPaperTradingUseCase()
        >>> await use_case.execute(
        ...     bot_id=8,
        ...     duration_minutes=60,
        ...     config=PaperTradingConfig(initial_balance=5000.0),
        ... )
    """

    async def execute(
        self,
        bot_id: int,
        duration_minutes: int,
        config: Optional[PaperTradingConfig] = None,
    ) -> dict:
        """Execute paper trading session.
        
        Args:
            bot_id: Bot ID to run
            duration_minutes: Session duration in minutes
            config: Paper trading configuration
        
        Returns:
            Session summary with performance metrics
        """
        logger.info(
            f"Starting paper trading session: bot {bot_id}, "
            f"{duration_minutes}min"
        )
        
        # Initialize engine
        engine = PaperTradingEngine(bot_id=bot_id, config=config)
        
        session_start = datetime.now()
        
        try:
            # Run trading loop
            await self._run_trading_loop(
                engine=engine,
                bot_id=bot_id,
                duration_minutes=duration_minutes,
            )
        except Exception as e:
            logger.error(f"Paper trading session failed: {e}", exc_info=True)
            raise
        finally:
            session_end = datetime.now()
            
            # Close all positions
            for position in engine.positions:
                try:
                    await engine.close_position(position.position_id)
                except Exception as e:
                    logger.warning(
                        f"Failed to close position {position.position_id}: {e}"
                    )
        
        # Generate summary
        summary = engine.get_performance_summary()
        summary.update({
            "bot_id": bot_id,
            "session_start": session_start.isoformat(),
            "session_end": session_end.isoformat(),
            "duration_minutes": (session_end - session_start).seconds / 60,
        })
        
        logger.info(
            f"Paper trading session completed: "
            f"P&L ${summary['total_pnl']:+.2f}, "
            f"ROI {summary['roi']:.2%}"
        )
        
        return summary

    async def _run_trading_loop(
        self,
        engine: PaperTradingEngine,
        bot_id: int,
        duration_minutes: int,
    ) -> None:
        """Run trading loop.
        
        Args:
            engine: Paper trading engine
            bot_id: Bot ID
            duration_minutes: Loop duration
        """
        end_time = datetime.now().timestamp() + (duration_minutes * 60)
        
        while datetime.now().timestamp() < end_time:
            try:
                # In real implementation:
                # 1. Fetch signals from SignalService
                # 2. Evaluate with BotService strategy
                # 3. Validate with RiskManager
                # 4. Place orders via engine
                
                # Simplified simulation for now
                await self._simulate_trading_cycle(engine, bot_id)
                
                # Wait before next cycle
                await asyncio.sleep(10)  # 10s cycle
                
            except Exception as e:
                logger.error(f"Trading cycle error: {e}", exc_info=True)
                await asyncio.sleep(30)  # Wait longer on error

    async def _simulate_trading_cycle(self, engine: PaperTradingEngine, bot_id: int) -> None:
        """Simulate one trading cycle.
        
        Args:
            engine: Paper trading engine
            bot_id: Bot ID
        """
        # This is a placeholder - real implementation would:
        # 1. Call SignalService.get_active_signals()
        # 2. Filter by bot_id and zone
        # 3. Evaluate with BotService.should_trade()
        # 4. Validate with RiskManager.validate_order()
        # 5. Place order via engine.place_order()
        
        # Example simulation:
        import random
        
        if random.random() < 0.1:  # 10% chance to trade
            try:
                await engine.place_order(
                    market_id=f"sim_market_{random.randint(1, 100)}",
                    side=OrderSide.YES if random.random() < 0.5 else OrderSide.NO,
                    size=random.uniform(10, 50),
                    price=random.uniform(0.45, 0.85),
                    order_type=OrderType.POST_ONLY,
                )
            except ValueError as e:
                logger.debug(f"Order rejected: {e}")
