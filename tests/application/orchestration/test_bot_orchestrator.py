"""Tests for bot orchestrator.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.orchestration.bot_orchestrator import (
    BotOrchestrator,
    OrchestratorConfig,
    OrchestratorState,
)
from src.domain.entities.bot import Bot, BotState, StrategyType


@pytest.fixture
def mock_bot():
    """Create mock bot."""
    return Bot(
        bot_id=8,
        strategy_type=StrategyType.TAIL_RISK,
        capital_allocated=5000.0,
        state=BotState.IDLE,
        created_at=datetime.now(),
    )


@pytest.fixture
def mock_bot_repository():
    """Create mock bot repository."""
    repo = AsyncMock()
    repo.update = AsyncMock()
    return repo


@pytest.fixture
def mock_position_service():
    """Create mock position service."""
    service = AsyncMock()
    service.get_open_positions = AsyncMock(return_value=[])
    return service


@pytest.fixture
def mock_risk_service():
    """Create mock risk service."""
    service = AsyncMock()
    service.trigger_circuit_breaker = AsyncMock()
    return service


@pytest.fixture
def orchestrator(mock_bot, mock_bot_repository, mock_position_service, mock_risk_service):
    """Create orchestrator instance."""
    config = OrchestratorConfig(
        health_check_interval_seconds=1,
        max_consecutive_errors=3,
    )
    return BotOrchestrator(
        bot=mock_bot,
        bot_repository=mock_bot_repository,
        position_service=mock_position_service,
        risk_service=mock_risk_service,
        config=config,
    )


@pytest.mark.asyncio
async def test_orchestrator_start(orchestrator, mock_bot_repository):
    """Test orchestrator start."""
    await orchestrator.start()
    
    assert orchestrator.state == OrchestratorState.RUNNING
    assert orchestrator._bot.state == BotState.RUNNING
    mock_bot_repository.update.assert_called()


@pytest.mark.asyncio
async def test_orchestrator_stop(orchestrator, mock_bot_repository):
    """Test orchestrator stop."""
    await orchestrator.start()
    await orchestrator.stop()
    
    assert orchestrator.state == OrchestratorState.STOPPED
    assert orchestrator._bot.state == BotState.IDLE
    mock_bot_repository.update.assert_called()


@pytest.mark.asyncio
async def test_orchestrator_pause_resume(orchestrator, mock_bot_repository):
    """Test orchestrator pause and resume."""
    await orchestrator.start()
    
    await orchestrator.pause()
    assert orchestrator.state == OrchestratorState.PAUSED
    assert orchestrator._bot.state == BotState.PAUSED
    
    await orchestrator.resume()
    assert orchestrator.state == OrchestratorState.RUNNING
    assert orchestrator._bot.state == BotState.RUNNING


@pytest.mark.asyncio
async def test_orchestrator_invalid_state_transition(orchestrator):
    """Test invalid state transition."""
    # Cannot pause before starting
    with pytest.raises(RuntimeError, match="Cannot pause from state IDLE"):
        await orchestrator.pause()
    
    # Cannot resume before pausing
    await orchestrator.start()
    with pytest.raises(RuntimeError, match="Cannot resume from state RUNNING"):
        await orchestrator.resume()


@pytest.mark.asyncio
async def test_orchestrator_close_positions_on_stop(orchestrator, mock_position_service):
    """Test positions closed on stop."""
    # Mock open positions
    mock_position = MagicMock()
    mock_position.position_id = 123
    mock_position_service.get_open_positions.return_value = [mock_position]
    
    await orchestrator.start()
    await orchestrator.stop()
    
    mock_position_service.close_position.assert_called_once_with(position_id=123)


@pytest.mark.asyncio
async def test_orchestrator_health_check_failure(orchestrator, mock_risk_service):
    """Test health check failure handling."""
    # Mock health check to fail
    with patch.object(
        orchestrator,
        "_perform_health_check",
        side_effect=Exception("Health check failed"),
    ):
        await orchestrator.start()
        
        # Wait for max consecutive errors
        await asyncio.sleep(4)  # 3 failures + buffer
        
        assert orchestrator.state == OrchestratorState.ERROR
        mock_risk_service.trigger_circuit_breaker.assert_called()
