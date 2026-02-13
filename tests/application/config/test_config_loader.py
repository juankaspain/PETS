"""Tests for config loader.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import pytest
from pydantic import ValidationError

from src.application.config.config_loader import (
    BotConfig,
    ConfigLoader,
    OrderExecution,
    StrategyParams,
)


@pytest.fixture
def config_loader():
    """Create config loader."""
    return ConfigLoader()


def test_load_bot_8_config(config_loader):
    """Test loading Bot 8 config."""
    config = config_loader.load_config("config/bot_8_config.yaml")
    
    assert config.bot_id == 8
    assert config.strategy_type == "TAIL_RISK"
    assert config.capital_allocated == 5000.0
    assert config.strategy_params.allowed_zones == [1, 2]
    assert config.strategy_params.kelly_fraction == 0.25
    assert config.order_execution.order_type == "POST_ONLY"


def test_validate_zone_constraints():
    """Test zone constraint validation."""
    # Valid: Z1-Z2
    valid_params = {
        "allowed_zones": [1, 2],
        "min_edge_z1": 0.15,
        "min_edge_z2": 0.10,
        "kelly_fraction": 0.25,
        "max_position_size": 1000.0,
        "max_open_positions": 5,
    }
    params = StrategyParams(**valid_params)
    assert params.allowed_zones == [1, 2]
    
    # Invalid: Z4-Z5 prohibited
    invalid_params = valid_params.copy()
    invalid_params["allowed_zones"] = [1, 2, 4]
    
    with pytest.raises(ValidationError, match="Only zones 1-2 allowed"):
        StrategyParams(**invalid_params)


def test_validate_kelly_fraction():
    """Test Kelly fraction validation."""
    # Valid: Half Kelly
    valid_params = {
        "allowed_zones": [1, 2],
        "min_edge_z1": 0.15,
        "min_edge_z2": 0.10,
        "kelly_fraction": 0.25,
        "max_position_size": 1000.0,
        "max_open_positions": 5,
    }
    params = StrategyParams(**valid_params)
    assert params.kelly_fraction == 0.25
    
    # Invalid: Full Kelly prohibited
    invalid_params = valid_params.copy()
    invalid_params["kelly_fraction"] = 0.8
    
    with pytest.raises(ValidationError, match="Full Kelly prohibited"):
        StrategyParams(**invalid_params)


def test_validate_order_type():
    """Test order type validation."""
    # Valid: POST_ONLY
    valid_order = {
        "order_type": "POST_ONLY",
        "time_in_force": "GTC",
        "max_slippage_bps": 10,
        "retry_attempts": 3,
        "retry_delay_seconds": 2.0,
    }
    order = OrderExecution(**valid_order)
    assert order.order_type == "POST_ONLY"
    
    # Invalid: Taker orders prohibited
    invalid_order = valid_order.copy()
    invalid_order["order_type"] = "MARKET"
    
    with pytest.raises(ValidationError, match="POST_ONLY required"):
        OrderExecution(**invalid_order)


def test_config_validation_comprehensive():
    """Test comprehensive config validation."""
    # This should load without errors
    loader = ConfigLoader()
    config = loader.load_config("config/bot_8_config.yaml")
    
    # Verify all Bot 8 constraints
    assert config.strategy_params.allowed_zones == [1, 2]  # Z1-Z2 only
    assert config.strategy_params.kelly_fraction <= 0.5    # Half Kelly max
    assert config.order_execution.order_type == "POST_ONLY"  # Maker only
    assert config.market_data.source == "POLYMARKET_WEBSOCKET"  # Real-time
    assert config.risk_limits.consecutive_loss_limit == 3  # Circuit breaker
    assert config.risk_limits.daily_loss_pct == 0.05       # 5% daily limit
    assert config.risk_limits.bot_drawdown_pct == 0.25     # 25% bot limit
