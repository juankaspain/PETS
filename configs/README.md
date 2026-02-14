# Bot Configurations

This directory contains individual configuration files for each trading bot in the PETS system.

## Directory Structure

```
configs/
  bot_01_rebalancer.yaml      # Bot 1: Portfolio Rebalancing
  bot_02_esports.yaml         # Bot 2: Esports Markets
  bot_03_copy_trading.yaml    # Bot 3: Copy Trading
  bot_04_news_driven.yaml     # Bot 4: News-Driven Trading
    bot_05_market_making.yaml     # Bot 5: Market Making
  bot_06_multi_outcome.yaml   # Bot 6: Multi-Outcome Markets
  bot_07_contrarian.yaml      # Bot 7: Contrarian Strategy
  bot_08_tail_risk.yaml       # Bot 8: Tail Risk Combo
  bot_09_advanced_kelly.yaml  # Bot 9: Advanced Kelly Criterion
  bot_10_longterm.yaml        # Bot 10: Long-term Holdings
```

## Configuration Schema

Each bot configuration file follows this structure:

```yaml
bot_id: <number>              # Unique bot identifier
strategy_type: <string>       # Strategy type identifier
capital_allocated: <float>    # Capital allocated to this bot

strategy_params:              # Strategy-specific parameters
  # Varies by bot type

order_execution:              # Order execution settings
  order_type: POST_ONLY       # Order type (maker/taker)
  time_in_force: GTC          # Time in force
  max_slippage_bps: <int>     # Max slippage in basis points

risk_limits:                  # Risk management settings
  consecutive_loss_limit: <int>
  daily_loss_pct: <float>
  bot_drawdown_pct: <float>

market_data:                  # Market data settings
  source: POLYMARKET_WEBSOCKET
  update_frequency_ms: <int>

monitoring:                   # Alerting and monitoring
  health_check_interval_seconds: <int>
  alert_channels: [EMAIL, TELEGRAM]

paper_trading:                # Paper trading mode
  enabled: <bool>
  initial_balance: <float>
```

## Usage

Configurations are loaded at bot startup:

```python
from src.config import load_bot_config

config = load_bot_config('bot_08_tail_risk')
bot = TailRiskComboStrategy(config)
```

## Environment Variables

Sensitive values should be stored in environment variables:

- `POLYMARKET_API_KEY` - API key for Polymarket
- `TELEGRAM_BOT_TOKEN` - Telegram bot token for alerts
- `WALLET_PRIVATE_KEY` - Wallet private key (NEVER commit this)

## Related Documentation

- [System Configuration](../config/README.md) - Global system settings
- [Bot Implementation](../src/bots/README.md) - Bot source code
- [Risk Management](../docs/risk_management.md) - Risk parameters guide
