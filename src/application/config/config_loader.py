"""Configuration loader and validator.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError, validator

logger = logging.getLogger(__name__)


class StrategyParams(BaseModel):
    """Strategy parameters."""

    allowed_zones: list[int] = Field(..., min_items=1, max_items=5)
    min_edge_z1: float = Field(..., ge=0.0, le=1.0)
    min_edge_z2: float = Field(..., ge=0.0, le=1.0)
    kelly_fraction: float = Field(..., ge=0.0, le=0.5)  # Max Half Kelly
    max_position_size: float = Field(..., gt=0)
    max_open_positions: int = Field(..., ge=1, le=20)

    @validator("allowed_zones")
    def validate_zones(cls, v):
        """Validate zone constraints."""
        if not all(1 <= z <= 5 for z in v):
            raise ValueError("Zones must be in range 1-5")
        
        # Bot 8 specific: Z1-Z2 only
        if set(v) - {1, 2}:
            raise ValueError(
                "Bot 8 constraint violated: Only zones 1-2 allowed. "
                "Directional zones 4-5 PROHIBITED."
            )
        
        return v

    @validator("kelly_fraction")
    def validate_kelly(cls, v):
        """Validate Kelly fraction."""
        if v > 0.5:
            raise ValueError(
                f"Full Kelly prohibited. Max 0.5 (Half Kelly), got {v}"
            )
        return v


class OrderExecution(BaseModel):
    """Order execution config."""

    order_type: str = Field(..., regex="^(POST_ONLY|LIMIT|MARKET)$")
    time_in_force: str = Field(..., regex="^(GTC|IOC|FOK)$")
    max_slippage_bps: int = Field(..., ge=0, le=100)
    retry_attempts: int = Field(..., ge=1, le=10)
    retry_delay_seconds: float = Field(..., ge=0.1, le=60.0)

    @validator("order_type")
    def validate_order_type(cls, v):
        """Validate order type."""
        # Bot 8 specific: POST_ONLY mandatory
        if v != "POST_ONLY":
            raise ValueError(
                f"Bot 8 constraint violated: POST_ONLY required, got {v}. "
                f"Taker orders PROHIBITED."
            )
        return v


class RiskLimits(BaseModel):
    """Risk limits config."""

    consecutive_loss_limit: int = Field(..., ge=1, le=10)
    daily_loss_pct: float = Field(..., ge=0.0, le=1.0)
    bot_drawdown_pct: float = Field(..., ge=0.0, le=1.0)
    portfolio_drawdown_pct: float = Field(..., ge=0.0, le=1.0)
    max_position_pct: float = Field(..., ge=0.0, le=1.0)
    max_exposure_pct: float = Field(..., ge=0.0, le=1.0)
    min_sharpe_ratio: float = Field(..., ge=0.0)
    max_correlation: float = Field(..., ge=0.0, le=1.0)


class MarketData(BaseModel):
    """Market data config."""

    source: str = Field(..., regex="^(POLYMARKET_WEBSOCKET|POLYMARKET_REST)$")
    update_frequency_ms: int = Field(..., ge=10, le=10000)
    lookback_period_days: int = Field(..., ge=1, le=365)
    min_liquidity_usd: float = Field(..., gt=0)

    @validator("source")
    def validate_source(cls, v):
        """Validate data source."""
        # Bot 8 specific: WebSocket required
        if v != "POLYMARKET_WEBSOCKET":
            raise ValueError(
                f"Bot 8 constraint violated: POLYMARKET_WEBSOCKET required, got {v}. "
                f"Real-time data MANDATORY."
            )
        return v


class BotConfig(BaseModel):
    """Bot configuration."""

    bot_id: int = Field(..., ge=1, le=10)
    strategy_type: str = Field(..., regex="^(TAIL_RISK|ARBITRAGE|MARKET_MAKING)$")
    capital_allocated: float = Field(..., ge=1000.0, le=10000.0)
    strategy_params: StrategyParams
    order_execution: OrderExecution
    risk_limits: RiskLimits
    market_data: MarketData
    wallet: Dict[str, Any]
    monitoring: Dict[str, Any]
    paper_trading: Dict[str, Any]
    logging: Dict[str, Any]
    metadata: Dict[str, Any]

    class Config:
        """Pydantic config."""
        extra = "forbid"  # Reject unknown fields


class ConfigLoader:
    """Load and validate bot configuration.
    
    Examples:
        >>> loader = ConfigLoader()
        >>> config = loader.load_config("config/bot_8_config.yaml")
        >>> print(config.bot_id)  # 8
    """

    def __init__(self, base_path: Optional[Path] = None) -> None:
        """Initialize config loader.
        
        Args:
            base_path: Base path for config files (defaults to project root)
        """
        self._base_path = base_path or Path(__file__).parent.parent.parent.parent

    def load_config(self, config_path: str) -> BotConfig:
        """Load and validate configuration.
        
        Args:
            config_path: Path to YAML config file (relative to base_path)
        
        Returns:
            Validated BotConfig
        
        Raises:
            FileNotFoundError: If config file not found
            ValidationError: If config validation fails
            yaml.YAMLError: If YAML parsing fails
        
        Examples:
            >>> loader = ConfigLoader()
            >>> config = loader.load_config("config/bot_8_config.yaml")
        """
        full_path = self._base_path / config_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Config file not found: {full_path}")
        
        logger.info(f"Loading config from: {full_path}")
        
        try:
            # Load YAML
            with open(full_path, "r") as f:
                raw_config = yaml.safe_load(f)
            
            # Substitute environment variables
            raw_config = self._substitute_env_vars(raw_config)
            
            # Validate and parse
            config = BotConfig(**raw_config)
            
            logger.info(
                f"Config loaded successfully: Bot {config.bot_id} - "
                f"{config.strategy_type}"
            )
            
            return config
        
        except ValidationError as e:
            logger.error(f"Config validation failed: {e}")
            raise
        
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing failed: {e}")
            raise

    def _substitute_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute environment variables in config.
        
        Args:
            config: Raw config dictionary
        
        Returns:
            Config with env vars substituted
        
        Examples:
            >>> # In YAML: api_key: ${POLYMARKET_API_KEY}
            >>> # After substitution: api_key: "actual_key_value"
        """
        # Recursive substitution for nested dicts
        if isinstance(config, dict):
            return {
                k: self._substitute_env_vars(v)
                for k, v in config.items()
            }
        
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            # Extract env var name
            env_var = config[2:-1]
            value = os.getenv(env_var)
            
            if value is None:
                logger.warning(
                    f"Environment variable not found: {env_var}. "
                    f"Using placeholder."
                )
                return config
            
            return value
        
        else:
            return config
