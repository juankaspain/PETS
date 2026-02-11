# 🚀 Polymarket Elite Trading System (PETS)

> **Professional-grade automated trading system for Polymarket prediction markets**
> 
> Built to operate in the **top 0.04% of traders** that capture 70% of profits

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-24.x-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Bot Strategies](#bot-strategies)
- [Dashboard](#dashboard)
- [Monitoring](#monitoring)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

PETS (Polymarket Elite Trading System) is a **production-grade automated trading platform** designed for Polymarket prediction markets. The system implements **10 professionally-audited strategies** based on analysis of 86 million historical trades and proven cases of $100K-$400K+ profits.

### Why PETS?

**The Reality**: 70% of 1.7M Polymarket traders lose money. Only 0.04% capture 70% of total profits.

**Our Mission**: Build a system that operates in that elite 0.04% through:
- ✅ **Professional risk management** (circuit breakers, Kelly Criterion, 5-zone framework)
- ✅ **Sub-100ms latency** (WebSocket-first architecture)
- ✅ **Proven strategies** (validated with real-world $100K+ profit cases)
- ✅ **Industrial monitoring** (Grafana + Prometheus + real-time dashboard)
- ✅ **Cost-optimized** ($80-178/month, 100% open-source)

---

## ✨ Key Features

### 🤖 **10 Professional Trading Bots**

| Bot | Strategy | Type | ROI Target | Evidence |
|-----|----------|------|------------|----------|
| **Bot 1** | Market Rebalancing Arbitrage | Agresivo | 8-15% | $39.5M extracted in 12 months |
| **Bot 2** | Esports & Live Events Parsing | Agresivo | 25-40% | >$200K documented profits |
| **Bot 3** | Copy Trading (Top Whales) | Agresivo | 15-25% | Top whale: $2.93M profit |
| **Bot 4** | News Scalping | Agresivo | 20-35% | 30-90s edge validated |
| **Bot 5** | Market Making | Neutro-Agresivo | 10-16% | 20% maker rebates |
| **Bot 6** | Multi-Outcome Arbitrage | Neutro-Agresivo | 12-20% | Used by elite whales |
| **Bot 7** | AI Contrarian + Attention | Neutro-Agresivo | 30-80% | 11,000% ROI backtested |
| **Bot 8** | Tail Risk + MM Combo | Neutro-Agresivo | 25-50% | planktonXD: $106K/year |
| **Bot 9** | Kelly Value Betting | Poco Agresivo | 6-12% | Mathematically optimal |
| **Bot 10** | Long-term Value | Poco Agresivo | 8-14% | Specialist advantage |

### 🛡️ **Enterprise-Grade Risk Management**

- **5-Zone Framework**: Automatic classification and restrictions (Zone 4-5 prohibited for directional bets)
- **Circuit Breakers**: Auto-halt after 3 consecutive losses or 5% daily loss
- **Half/Quarter Kelly**: Optimal position sizing with error tolerance
- **Drawdown Limits**: 25% individual bot, 40% total portfolio

### 📊 **Real-Time Dashboard**

- **Bot Control Panel**: Start/stop individual bots or all at once
- **Live Metrics**: ROI, Sharpe ratio, drawdown, win rate (1s updates)
- **P&L Charts**: Real-time candlestick and line charts
- **Position Monitor**: Live position tracking with zone classification
- **Risk Alerts**: Visual alerts for circuit breakers and limit violations

### 🔬 **Advanced Monitoring**

- **Grafana Dashboards**: 4 pre-configured dashboards (bot performance, system health, orders, risk)
- **Prometheus Metrics**: 20+ custom metrics with 15s scraping
- **Structured Logging**: JSON logs with ELK-ready format
- **Telegram/Discord Alerts**: Real-time notifications for critical events

### 🚀 **Performance Optimizations**

- **WebSocket-First**: <100ms latency to Polymarket (vs 500ms+ REST)
- **Redis Pub/Sub**: <10ms message broadcasting
- **TimescaleDB**: 10-100x faster time-series queries with hypertables
- **Post-Only Orders**: 0% taker fees + 20% maker rebates

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DASHBOARD (Streamlit)                     │
│  Bot Control | Metrics | P&L Charts | Positions | Alerts    │
└──────────────────┬──────────────────────────────────────────┘
                   │ WebSocket + REST API
┌──────────────────▼──────────────────────────────────────────┐
│                    INTERNAL API (FastAPI)                    │
│  /bots | /positions | /orders | /metrics | /health          │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                      CORE SERVICES                           │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ WebSocket  │  │ Market Data  │  │ Order Execution    │  │
│  │ Gateway    │  │ Processor    │  │ Engine             │  │
│  └────────────┘  └──────────────┘  └────────────────────┘  │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ Risk       │  │ Position     │  │ Event Bus          │  │
│  │ Manager    │  │ Tracker      │  │ (Redis Pub/Sub)    │  │
│  └────────────┘  └──────────────┘  └────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    BOT STRATEGY LAYER                        │
│  Bot 1-10 (each runs independently in Docker container)     │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                       DATA LAYER                             │
│  ┌────────────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │ TimescaleDB    │  │ Redis      │  │ External APIs    │  │
│  │ (PostgreSQL)   │  │ Cache      │  │ (Polymarket/News)│  │
│  └────────────────┘  └────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Key Design Decisions**:
1. **Event-Driven Microservices**: Redis Pub/Sub for <10ms inter-service communication
2. **WebSocket Gateway**: Centralized connection to Polymarket (vs 10 redundant connections)
3. **Docker Compose**: Orchestration without Kubernetes overhead (<20 bots)
4. **TimescaleDB**: PostgreSQL + automatic time-series partitioning
5. **Post-Only Orders**: Mandatory for 0% fees + 20% maker rebates

---

## 📦 Prerequisites

### Required

- **Docker 24.x+** and **Docker Compose 2.x+**
- **Python 3.11+** (for development only)
- **Git** (for cloning repository)
- **8GB+ RAM** (16GB recommended for production)
- **50GB+ disk space** (for TimescaleDB data)

### Recommended for Production

- **VPS**: DigitalOcean NYC3 or AWS us-east-1
  - 8 vCPU, 16GB RAM, 200GB NVMe SSD
  - 1-5ms latency to Polygon nodes
  - Cost: $80-120/month

### API Keys & Accounts

- **Polymarket API Key** (free, requires KYC)
- **Polygon RPC** (Alchemy/Infura free tier: 300M requests/month)
- **News APIs** (optional): Reuters, Bloomberg trial or RSS feeds
- **Esports APIs** (optional): Riot Games, Steam, Abios (free tiers available)

---

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/polymarket-elite-trading-system.git
cd polymarket-elite-trading-system
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys and configuration
nano .env  # or your preferred editor
```

**Minimum required in `.env`**:
```bash
# Polymarket
POLYMARKET_API_KEY=your_api_key_here
POLYMARKET_API_SECRET=your_api_secret_here
POLYMARKET_WALLET_PRIVATE_KEY=your_wallet_private_key_here

# Database
DB_PASSWORD=your_secure_password_here

# Monitoring
GRAFANA_PASSWORD=your_grafana_password_here

# APIs (optional)
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY
```

### 3. Initialize System

```bash
# Setup database and configuration
make setup

# This will:
# - Create Docker volumes
# - Initialize TimescaleDB hypertables
# - Validate configuration files
# - Run health checks
```

### 4. Start Services

```bash
# Start all services (development mode with hot-reload)
make start-dev

# Or for production mode
make start
```

### 5. Access Dashboard

Open your browser and navigate to:

- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (user: admin, password: from .env)
- **Prometheus**: http://localhost:9090

### 6. Start Your First Bot

Via Dashboard:
1. Navigate to "Bot Control" page
2. Click "▶️ Start" on Bot 8 (Tail Risk + MM Combo)
3. Monitor metrics in real-time

Via CLI:
```bash
# Start specific bot
make start-bot BOT_ID=8

# Start all bots
make start-all-bots

# Stop specific bot
make stop-bot BOT_ID=8

# Emergency halt all bots
make emergency-halt
```

---

## ⚙️ Configuration

### Bot Configuration

Each bot has a YAML config file in `config/bots/`:

```yaml
# config/bots/bot_08_tail_risk_combo.yaml
bot_id: 8
name: "Tail Risk + MM Combo"
enabled: true
strategy_type: "neutro-agresivo"

capital:
  allocation_percentage: 14  # 14% of total capital
  min_position_size_usd: 10
  max_position_size_usd: 500

risk_management:
  max_drawdown_percentage: 25
  max_consecutive_losses: 3
  daily_loss_limit_percentage: 5
  zone_restrictions:
    - zone: 1  # Tail risk ONLY in Zone 1
      allowed: true
      max_exposure_percentage: 30

tail_risk:
  min_price: 0.001  # 0.1¢
  max_price: 0.05   # 5¢
  max_positions: 50
  position_size_usd: 20

market_making:
  volatility_threshold: 0.05  # <5% 14-day volatility
  spread_percentage: 0.02     # 2% spread
  rebalance_interval_minutes: 15
```

### Risk Management Configuration

Global risk rules in `config/risk_management.yaml`:

```yaml
global_limits:
  max_capital_per_strategy: 0.05      # 5% max per strategy
  max_capital_per_bot: 0.20           # 20% max per bot
  max_category_exposure: 0.60         # 60% max in one category
  total_max_drawdown: 0.40            # 40% halt threshold

circuit_breakers:
  consecutive_losses:
    threshold: 3
    action: "pause_bot"
    cooldown_hours: 24
  
  daily_loss:
    threshold_percentage: 5
    action: "halt_trading"
  
  drawdown:
    individual_threshold: 0.25
    portfolio_threshold: 0.40
    action: "emergency_halt"

position_sizing:
  kelly_fraction: 0.5  # Half Kelly (safer than Full Kelly)
  min_kelly_fraction: 0.25
  max_leverage: 1.0    # No leverage
```

### Zone Framework Configuration

5-zone price classification in `config/zone_framework.yaml`:

```yaml
zones:
  zone_1:
    range: [0.05, 0.20]
    risk_reward: "1:4 to 1:19"
    allowed_strategies:
      - "tail_risk"
      - "contrarian"
      - "value_betting"
    restrictions: []
  
  zone_2:
    range: [0.20, 0.40]
    risk_reward: "1:1.5 to 1:4"
    allowed_strategies:
      - "value_betting"
      - "news_scalping"
      - "copy_trading"
    restrictions: []
  
  zone_3:
    range: [0.40, 0.60]
    risk_reward: "~1:1"
    allowed_strategies:
      - "arbitrage"
      - "market_making"
    restrictions:
      - "directional_bets_require_edge_gt_0.52"
  
  zone_4:
    range: [0.60, 0.80]
    risk_reward: "1:0.25 to 1:0.67"
    allowed_strategies:
      - "market_making"
      - "arbitrage"
    restrictions:
      - "directional_bets_prohibited"  # CRITICAL
  
  zone_5:
    range: [0.80, 0.98]
    risk_reward: "1:0.02 to 1:0.25"
    allowed_strategies:
      - "internal_arbitrage"
    restrictions:
      - "directional_bets_prohibited"  # CRITICAL
```

---

## 🤖 Bot Strategies

### Detailed Strategy Overview

#### **Bot 1: Market Rebalancing Arbitrage** (Agresivo)
- **What**: Exploits YES+NO≠$1.00 in individual markets
- **How**: Scans 500+ markets every 30s, buys both sides when sum <$1
- **Evidence**: $39.5M extracted in 12 months (86M trades analyzed)
- **Risk**: Latency-sensitive, 500ms-1h execution delays destroy profit
- **Capital**: $6,000 (12% allocation)

#### **Bot 2: Esports & Live Events Parsing** (Agresivo)  
- **What**: Connects to official game APIs (LoL, Dota 2, VALORANT) for 30-40s edge
- **How**: Monitors in-game events (kills, objectives) before stream delays
- **Evidence**: >$200K documented profits, 5-15% divergence vs bookmakers
- **Risk**: API dependency, requires expertise in esports
- **Capital**: $7,000 (14% allocation)

#### **Bot 8: Tail Risk + MM Combo** (Neutro-Agresivo) ⭐ **BEST EVIDENCE**
- **What**: Combines tail risk (0.1-5¢ bets) with market making for stability
- **How**: 20-50 diversified tail positions + continuous market making
- **Evidence**: planktonXD $106K in 61K trades (170/day), biggest win only $2,527
- **Risk**: 80-90% tail positions expire worthless, requires extreme patience
- **Capital**: $7,000 (14% allocation)

> See full strategy details in [docs/STRATEGY_GUIDE.md](docs/STRATEGY_GUIDE.md)

---

## 📊 Dashboard

### Overview Page

The main dashboard provides at-a-glance monitoring:

**Top Section - Control Panel**:
```
┌───────────────────────────────────────────────────┐
│  🔴 EMERGENCY HALT ALL   🟢 START ALL   🟡 STOP  │
└───────────────────────────────────────────────────┘
```

**Metrics Cards** (1s updates):
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Total ROI    │ Sharpe Ratio │ Max Drawdown │ Win Rate     │
│ +12.3% ⬆️    │ 1.45 🟢      │ -8.2% 🟢     │ 58.3% 🟢     │
│ $6,150       │ (target:1.2) │ (limit: 25%) │ (target:55%) │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

**P&L Chart**:
- Real-time line chart with 10 bot lines (color-coded)
- Candlestick view for OHLC data
- Zoom, pan, hover tooltips

**Position Table** (live):
| Bot | Market | Side | Size | Entry | Current | P&L | Zone | Duration |
|-----|--------|------|------|-------|---------|-----|------|----------|
| 8 | VALORANT Fuego | YES | 100 | $0.10 | $0.15 | +50% | Z1 | 2h 15m |

### Bot Control Page

Individual bot controls with status indicators:

```
Bot 1: Market Rebalancing Arbitrage
Status: 🟢 RUNNING
[⏸️ Pause] [⏹️ Stop] [⚙️ Config]

Performance Today:
- Trades: 47
- Win Rate: 72.3%
- P&L: +$142 (+2.4%)
- Avg Latency: 87ms
```

### Risk Monitor Page

Real-time risk metrics:

- **Zone Distribution Heatmap**: Visual representation of capital by zone
- **Circuit Breaker Status**: Active/Triggered/OK for all bots
- **Consecutive Loss Counters**: Warning at 2, halt at 3
- **Drawdown Gauges**: Individual (25% limit) and portfolio (40% limit)

---

## 📈 Monitoring

### Grafana Dashboards

4 pre-configured dashboards accessible at `http://localhost:3000`:

1. **Bot Performance**
   - ROI by bot (line chart)
   - Sharpe ratio trend
   - Win rate distribution
   - Trade frequency heatmap

2. **System Health**
   - CPU/Memory/Disk usage
   - WebSocket latency (p50, p95, p99)
   - API request duration
   - Error rate

3. **Order Execution**
   - Fill rate (target: >95%)
   - Slippage distribution
   - Post-only vs taker orders
   - Rejected orders

4. **Risk Metrics**
   - Drawdown by bot
   - Zone exposure heatmap
   - Consecutive losses
   - Circuit breaker triggers

### Prometheus Metrics

20+ custom metrics exported at `http://localhost:8000/metrics`:

```
# Bot trading metrics
bot_trades_total{bot_id="8", side="YES", zone="1"} 142
bot_pnl_usd{bot_id="8"} 6150.32
bot_win_rate{bot_id="8"} 0.583

# System metrics
websocket_latency_ms{percentile="p95"} 87.3
api_request_duration_seconds{endpoint="/orders", method="POST"} 0.142

# Risk metrics
consecutive_losses_count{bot_id="8"} 0
drawdown_percentage{bot_id="8"} 0.082
circuit_breaker_triggered_total{bot_id="8", type="consecutive_losses"} 0
```

### Alerting

Telegram/Discord alerts for critical events:

- ⚠️ Circuit breaker triggered
- 🚨 Drawdown approaching limit (20% individual, 35% portfolio)
- ❌ WebSocket disconnection
- ⏰ Daily P&L summary (configurable time)
- 🎯 Major win (>$1000 single trade)

---

## 🛠️ Development

### Setup Development Environment

```bash
# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Start services in development mode (hot-reload)
make start-dev
```

### Code Quality Tools

```bash
# Format code
make format

# Run linters
make lint

# Type checking
make type-check

# All quality checks
make quality
```

### Hot Reload

Development mode includes hot-reload for rapid iteration:

```bash
# Start with hot-reload (changes auto-reload)
make start-dev

# Logs will show:
# "Detected change in src/bots/bot_08_tail_risk_combo.py"
# "Reloading bot_08..."
```

---

## 🧪 Testing

### Run Test Suite

```bash
# Run all tests
make test

# Run specific test categories
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-e2e           # End-to-end tests only

# Run with coverage report
make test-coverage

# Run specific test file
pytest tests/unit/test_risk_manager.py -v
```

### Test Categories

**Unit Tests** (`tests/unit/`):
- Isolated component testing
- Mocked external dependencies
- Fast execution (<1s total)

**Integration Tests** (`tests/integration/`):
- Multi-component interactions
- Real DB/Redis (test containers)
- Moderate execution (~30s total)

**E2E Tests** (`tests/e2e/`):
- Full bot lifecycle (start → trade → stop)
- Real external APIs (with mocks for expensive calls)
- Slow execution (~5min total)

### Paper Trading Mode

Test strategies with simulated capital:

```bash
# Start specific bot in paper trading mode
python scripts/paper_trade.py --bot-id 8 --duration-days 30

# Monitor in dashboard (P&L will show "SIMULATED")
```

---

## 🚀 Deployment

### Local Development

```bash
make start-dev  # Hot-reload enabled
```

### VPS Production

```bash
# 1. Provision VPS (DigitalOcean NYC3 recommended)
# 2. Install Docker + Docker Compose
# 3. Clone repository
git clone https://github.com/yourusername/polymarket-elite-trading-system.git
cd polymarket-elite-trading-system

# 4. Configure production environment
cp .env.example .env
nano .env  # Fill with production values

# 5. Deploy
make deploy-prod

# 6. Verify health
make health-check
```

### Monitoring Production

```bash
# View logs
make logs              # All services
make logs-bot-08       # Specific bot

# Database shell
make shell-db

# Redis CLI
make shell-redis

# Backup database
make backup-db
```

### Scaling to Kubernetes

When you scale >20 bots:

```bash
# Deploy to K8s cluster
kubectl apply -f infra/kubernetes/

# Verify deployment
kubectl get pods -n pets

# Scale bot replicas
kubectl scale deployment bot-08 --replicas=3 -n pets
```

---

## 📚 Documentation

Comprehensive documentation in `docs/`:

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: System architecture deep-dive
- **[STRATEGY_GUIDE.md](docs/STRATEGY_GUIDE.md)**: All 10 strategies explained
- **[RISK_MANAGEMENT.md](docs/RISK_MANAGEMENT.md)**: 5-zone framework, Kelly Criterion
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)**: Production deployment guide
- **[DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)**: TimescaleDB schema reference
- **[MONITORING.md](docs/MONITORING.md)**: Grafana/Prometheus setup
- **[API_REFERENCE.md](docs/API_REFERENCE.md)**: Internal API documentation
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)**: Common issues & solutions

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-strategy`)
3. Make your changes with tests
4. Run quality checks (`make quality`)
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

### Code Standards

- **Python**: Black formatting, Ruff linting, MyPy type hints
- **Tests**: Minimum 80% coverage for new code
- **Documentation**: Update relevant docs for features
- **Commits**: Conventional Commits format

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

**Important**: This software is provided for educational and research purposes only.

- **Trading Risk**: All trading involves risk. Past performance does not guarantee future results.
- **Capital Loss**: You can lose all invested capital. Never trade with money you cannot afford to lose.
- **No Warranty**: This software is provided "as is" without warranty of any kind.
- **Regulatory**: Ensure compliance with local regulations. Polymarket is restricted in some jurisdictions.
- **Not Financial Advice**: This is not financial advice. Consult a financial advisor before trading.

**The developers assume no liability for financial losses incurred through use of this software.**

---

## 🙏 Acknowledgments

Built on the shoulders of giants:

- **Research**: Analysis of 86M Polymarket trades by IMDEA Networks
- **Case Studies**: planktonXD ($106K), gmpm ($2.93M), documented esports traders
- **Evidence**: 70% loss rate data from on-chain analysis of 1.7M addresses
- **Community**: Polymarket traders who shared strategies and lessons learned

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/polymarket-elite-trading-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/polymarket-elite-trading-system/discussions)
- **Discord**: [Join our Discord](https://discord.gg/your-server) (for community support)
- **Email**: support@yourproject.com (for critical issues)

---

## 📊 Project Stats

![GitHub stars](https://img.shields.io/github/stars/yourusername/polymarket-elite-trading-system?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/polymarket-elite-trading-system?style=social)
![GitHub issues](https://img.shields.io/github/issues/yourusername/polymarket-elite-trading-system)
![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/polymarket-elite-trading-system)

---

**Built with ❤️ by traders, for traders. Trade smart, trade safe.**
