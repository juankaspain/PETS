"""Unit tests for BaseBotStrategy abstract class."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.bots.base_bot import BaseBotStrategy, BotState, BotMetrics


class MockBot(BaseBotStrategy):
    """Mock bot for testing BaseBotStrategy."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initialize_called = False
        self.execute_cycle_called = False
        self.execute_cycle_count = 0
        self.stop_gracefully_called = False
        self.should_fail_initialize = False
        self.should_fail_cycle = False

    async def initialize(self) -> None:
        """Mock initialize."""
        if self.should_fail_initialize:
            raise RuntimeError("Initialize failed")
        self.initialize_called = True
        await asyncio.sleep(0.01)

    async def execute_cycle(self) -> None:
        """Mock execute_cycle."""
        if self.should_fail_cycle:
            raise RuntimeError("Cycle failed")
        self.execute_cycle_called = True
        self.execute_cycle_count += 1
        await asyncio.sleep(0.01)

    async def stop_gracefully(self) -> None:
        """Mock stop_gracefully."""
        self.stop_gracefully_called = True
        await asyncio.sleep(0.01)


@pytest.fixture
def base_config():
    """Base bot configuration."""
    return {
        "capital_allocated": 1000,
        "max_positions": 5,
        "cycle_interval_seconds": 0.05,  # Fast for testing
    }


class TestBaseBotInitialization:
    """Test bot initialization and config validation."""

    def test_valid_initialization(self, base_config):
        """Test bot initializes with valid config."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        assert bot.bot_id == 1
        assert bot.strategy_type == "test"
        assert bot.get_state() == BotState.IDLE
        assert bot.config == base_config

    def test_missing_capital_allocated(self, base_config):
        """Test initialization fails without capital_allocated."""
        del base_config["capital_allocated"]
        with pytest.raises(ValueError, match="Missing required config key"):
            MockBot(bot_id=1, strategy_type="test", config=base_config)

    def test_missing_max_positions(self, base_config):
        """Test initialization fails without max_positions."""
        del base_config["max_positions"]
        with pytest.raises(ValueError, match="Missing required config key"):
            MockBot(bot_id=1, strategy_type="test", config=base_config)

    def test_missing_cycle_interval(self, base_config):
        """Test initialization fails without cycle_interval_seconds."""
        del base_config["cycle_interval_seconds"]
        with pytest.raises(ValueError, match="Missing required config key"):
            MockBot(bot_id=1, strategy_type="test", config=base_config)

    def test_zero_capital(self, base_config):
        """Test initialization fails with zero capital."""
        base_config["capital_allocated"] = 0
        with pytest.raises(ValueError, match="capital_allocated must be > 0"):
            MockBot(bot_id=1, strategy_type="test", config=base_config)

    def test_negative_capital(self, base_config):
        """Test initialization fails with negative capital."""
        base_config["capital_allocated"] = -100
        with pytest.raises(ValueError, match="capital_allocated must be > 0"):
            MockBot(bot_id=1, strategy_type="test", config=base_config)

    def test_zero_max_positions(self, base_config):
        """Test initialization fails with zero max_positions."""
        base_config["max_positions"] = 0
        with pytest.raises(ValueError, match="max_positions must be > 0"):
            MockBot(bot_id=1, strategy_type="test", config=base_config)


class TestBotLifecycle:
    """Test bot lifecycle: start, pause, resume, stop."""

    @pytest.mark.asyncio
    async def test_start_bot(self, base_config):
        """Test bot starts successfully."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        await bot.start()
        await asyncio.sleep(0.1)  # Let it run a few cycles

        assert bot.get_state() == BotState.ACTIVE
        assert bot.initialize_called
        assert bot.execute_cycle_called
        assert bot.is_running()

        await bot.stop()

    @pytest.mark.asyncio
    async def test_start_already_running(self, base_config):
        """Test starting already running bot fails."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        await bot.start()
        await asyncio.sleep(0.05)

        with pytest.raises(RuntimeError, match="Cannot start bot in state"):
            await bot.start()

        await bot.stop()

    @pytest.mark.asyncio
    async def test_pause_resume_bot(self, base_config):
        """Test bot can be paused and resumed."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        await bot.start()
        await asyncio.sleep(0.1)

        # Pause
        await bot.pause()
        assert bot.get_state() == BotState.PAUSED
        assert bot.is_running()  # Still running but paused

        cycles_before = bot.execute_cycle_count
        await asyncio.sleep(0.1)  # Wait while paused
        cycles_after = bot.execute_cycle_count
        # Should not execute cycles while paused
        assert cycles_after == cycles_before

        # Resume
        await bot.resume()
        assert bot.get_state() == BotState.ACTIVE
        await asyncio.sleep(0.1)
        assert bot.execute_cycle_count > cycles_after

        await bot.stop()

    @pytest.mark.asyncio
    async def test_stop_bot(self, base_config):
        """Test bot stops gracefully."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        await bot.start()
        await asyncio.sleep(0.1)

        await bot.stop()

        assert bot.get_state() == BotState.STOPPED
        assert bot.stop_gracefully_called
        assert not bot.is_running()

    @pytest.mark.asyncio
    async def test_stop_not_running(self, base_config):
        """Test stopping idle bot fails."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        with pytest.raises(RuntimeError, match="Cannot stop bot in state"):
            await bot.stop()


class TestStateTransitions:
    """Test bot state machine transitions."""

    @pytest.mark.asyncio
    async def test_state_idle_to_active(self, base_config):
        """Test IDLE → STARTING → ACTIVE transition."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        assert bot.get_state() == BotState.IDLE

        await bot.start()
        await asyncio.sleep(0.05)

        assert bot.get_state() == BotState.ACTIVE
        await bot.stop()

    @pytest.mark.asyncio
    async def test_state_active_to_paused(self, base_config):
        """Test ACTIVE → PAUSED transition."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        await bot.start()
        await asyncio.sleep(0.05)

        await bot.pause()
        assert bot.get_state() == BotState.PAUSED

        await bot.stop()

    @pytest.mark.asyncio
    async def test_state_paused_to_active(self, base_config):
        """Test PAUSED → ACTIVE transition."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        await bot.start()
        await asyncio.sleep(0.05)
        await bot.pause()

        await bot.resume()
        assert bot.get_state() == BotState.ACTIVE

        await bot.stop()

    @pytest.mark.asyncio
    async def test_state_active_to_stopped(self, base_config):
        """Test ACTIVE → STOPPING → STOPPED transition."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        await bot.start()
        await asyncio.sleep(0.05)

        await bot.stop()
        assert bot.get_state() == BotState.STOPPED

    @pytest.mark.asyncio
    async def test_emergency_halt_any_state(self, base_config):
        """Test emergency halt from any state."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        await bot.start()
        await asyncio.sleep(0.05)

        await bot.emergency_halt()
        assert bot.get_state() == BotState.EMERGENCY_HALT


class TestErrorHandling:
    """Test error handling and recovery."""

    @pytest.mark.asyncio
    async def test_initialization_failure(self, base_config):
        """Test bot handles initialization failure."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        bot.should_fail_initialize = True

        with pytest.raises(RuntimeError, match="Initialize failed"):
            await bot.start()

        assert bot.get_state() == BotState.ERROR

    @pytest.mark.asyncio
    async def test_cycle_error_recovery(self, base_config):
        """Test bot logs cycle errors and continues."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        await bot.start()
        await asyncio.sleep(0.05)

        # Inject error
        bot.should_fail_cycle = True
        await asyncio.sleep(0.1)  # Let it error

        assert bot._errors_count > 0
        # Bot should still be running (not emergency halted yet)
        # unless it hit 5 consecutive errors

        await bot.stop()

    @pytest.mark.asyncio
    async def test_emergency_halt_after_5_errors(self, base_config):
        """Test bot emergency halts after 5 consecutive errors."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        bot.should_fail_cycle = True  # Every cycle will fail
        await bot.start()

        # Wait for 5 errors to accumulate
        await asyncio.sleep(0.5)

        # Should have emergency halted
        assert bot.get_state() == BotState.EMERGENCY_HALT


class TestMetrics:
    """Test bot metrics tracking."""

    def test_initial_metrics(self, base_config):
        """Test initial metrics state."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        metrics = bot.get_metrics()

        assert metrics.bot_id == 1
        assert metrics.strategy_type == "test"
        assert metrics.state == BotState.IDLE
        assert metrics.uptime_seconds == 0.0
        assert metrics.cycles_completed == 0
        assert metrics.errors_count == 0

    @pytest.mark.asyncio
    async def test_metrics_update_during_run(self, base_config):
        """Test metrics update during bot execution."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        await bot.start()
        await asyncio.sleep(0.2)  # Run for a bit

        metrics = bot.get_metrics()
        assert metrics.state == BotState.ACTIVE
        assert metrics.uptime_seconds > 0
        assert metrics.cycles_completed > 0
        assert metrics.last_cycle_duration_ms > 0

        await bot.stop()

    @pytest.mark.asyncio
    async def test_metrics_to_dict(self, base_config):
        """Test metrics serialization to dict."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        await bot.start()
        await asyncio.sleep(0.1)

        metrics = bot.get_metrics()
        metrics_dict = metrics.to_dict()

        assert isinstance(metrics_dict, dict)
        assert metrics_dict["bot_id"] == 1
        assert metrics_dict["strategy_type"] == "test"
        assert "state" in metrics_dict
        assert "uptime_seconds" in metrics_dict

        await bot.stop()


class TestIsRunning:
    """Test is_running helper method."""

    def test_is_running_idle(self, base_config):
        """Test is_running returns False when IDLE."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        assert not bot.is_running()

    @pytest.mark.asyncio
    async def test_is_running_active(self, base_config):
        """Test is_running returns True when ACTIVE."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        await bot.start()
        await asyncio.sleep(0.05)

        assert bot.is_running()
        await bot.stop()

    @pytest.mark.asyncio
    async def test_is_running_paused(self, base_config):
        """Test is_running returns True when PAUSED."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        await bot.start()
        await asyncio.sleep(0.05)
        await bot.pause()

        assert bot.is_running()  # PAUSED still counts as running
        await bot.stop()

    @pytest.mark.asyncio
    async def test_is_running_stopped(self, base_config):
        """Test is_running returns False when STOPPED."""
        bot = MockBot(bot_id=1, strategy_type="test", config=base_config)
        await bot.start()
        await asyncio.sleep(0.05)
        await bot.stop()

        assert not bot.is_running()
