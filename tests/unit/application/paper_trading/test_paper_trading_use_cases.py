"""Unit tests for paper trading use cases.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import pytest

from src.application.paper_trading.paper_trading_engine import (
    PaperTradingConfig,
    PaperTradingEngine,
)
from src.application.use_cases.paper_trading import (
    GetPaperTradingStatsUseCase,
    ResetPaperTradingUseCase,
    RunPaperTradingUseCase,
)


@pytest.fixture
def engine() -> PaperTradingEngine:
    """Create test engine."""
    config = PaperTradingConfig(
        initial_balance=5000.0,
        simulate_latency_ms=1,  # Very fast for tests
    )
    return PaperTradingEngine(bot_id=8, config=config)


class TestRunPaperTradingUseCase:
    """Test RunPaperTradingUseCase."""

    @pytest.mark.asyncio
    async def test_execute_short_session(self) -> None:
        """Test short trading session."""
        use_case = RunPaperTradingUseCase()
        
        config = PaperTradingConfig(
            initial_balance=5000.0,
            simulate_latency_ms=1,
        )
        
        # Run very short session
        summary = await use_case.execute(
            bot_id=8,
            duration_minutes=0.1,  # 6 seconds
            config=config,
        )
        
        assert "bot_id" in summary
        assert "session_start" in summary
        assert "session_end" in summary
        assert "total_pnl" in summary
        assert "roi" in summary
        assert summary["bot_id"] == 8


class TestGetPaperTradingStatsUseCase:
    """Test GetPaperTradingStatsUseCase."""

    @pytest.mark.asyncio
    async def test_get_stats(self, engine: PaperTradingEngine) -> None:
        """Test statistics retrieval."""
        use_case = GetPaperTradingStatsUseCase()
        
        stats = await use_case.execute(engine=engine)
        
        assert "balance" in stats
        assert "positions" in stats
        assert "metrics" in stats
        assert "roi" in stats
        
        # Verify balance structure
        assert "available" in stats["balance"]
        assert "reserved" in stats["balance"]
        assert "total" in stats["balance"]
        
        # Verify metrics
        assert "total_return_pct" in stats["metrics"]
        assert "total_pnl_usd" in stats["metrics"]
        assert "fees_paid_usd" in stats["metrics"]


class TestResetPaperTradingUseCase:
    """Test ResetPaperTradingUseCase."""

    @pytest.mark.asyncio
    async def test_reset_engine(self, engine: PaperTradingEngine) -> None:
        """Test engine reset."""
        # Modify state
        engine._realized_pnl = 100.0
        engine._balance.available = 4500.0
        
        use_case = ResetPaperTradingUseCase()
        result = await use_case.execute(engine=engine)
        
        assert result["status"] == "success"
        assert "bot" in result["message"]
        
        # Verify reset
        assert engine.balance.available == 5000.0
        assert engine._realized_pnl == 0.0
