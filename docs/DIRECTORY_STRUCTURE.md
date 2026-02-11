# Polymarket Elite Trading System (PETS) - Directory Structure

## Complete Project Structure

```
polymarket-elite-trading-system/
│
├── README.md                          # Project overview, quick start, architecture overview
├── LICENSE                            # MIT License
├── .gitignore                         # Python, Docker, IDE, data files
├── .env.example                       # Environment variables template (never commit .env)
├── .dockerignore                      # Files to exclude from Docker builds
├── docker-compose.yml                 # Production orchestration (all services)
├── docker-compose.dev.yml             # Development overrides (hot reload, debug)
├── docker-compose.test.yml            # Testing environment
├── Makefile                           # Convenience commands (make start, test, logs)
├── setup.py                           # Python package configuration
├── requirements.txt                   # Python dependencies (pinned versions)
├── requirements-dev.txt               # Development dependencies (pytest, black, etc.)
├── pyproject.toml                     # Black, Ruff, MyPy configuration
├── pytest.ini                         # Pytest configuration
├── .pre-commit-config.yaml            # Pre-commit hooks (linting, formatting)
│
├── docs/                              # 📚 Documentation
│   ├── README.md                      # Documentation index
│   ├── ARCHITECTURE.md                # System architecture with diagrams
│   ├── DEPLOYMENT.md                  # Deployment guide (local → VPS → K8s)
│   ├── STRATEGY_GUIDE.md              # Detailed explanation of 10 strategies
│   ├── RISK_MANAGEMENT.md             # 5-zone framework, Kelly, circuit breakers
│   ├── API_REFERENCE.md               # Internal API documentation
│   ├── DATABASE_SCHEMA.md             # TimescaleDB schema and queries
│   ├── MONITORING.md                  # Grafana/Prometheus setup
│   ├── TROUBLESHOOTING.md             # Common issues and solutions
│   ├── CONTRIBUTING.md                # Contribution guidelines
│   ├── CHANGELOG.md                   # Version history
│   └── diagrams/                      # Architecture diagrams (draw.io, mermaid)
│       ├── system_architecture.png
│       ├── data_flow.png
│       ├── deployment_topology.png
│       └── bot_lifecycle.png
│
├── config/                            # ⚙️ Configuration Files
│   │
│   ├── bots/                          # Bot-specific configurations
│   │   ├── bot_01_market_rebalancing.yaml
│   │   ├── bot_02_esports_parsing.yaml
│   │   ├── bot_03_copy_trading.yaml
│   │   ├── bot_04_news_scalping.yaml
│   │   ├── bot_05_market_making.yaml
│   │   ├── bot_06_multi_outcome_arb.yaml
│   │   ├── bot_07_contrarian_attention.yaml
│   │   ├── bot_08_tail_risk_combo.yaml
│   │   ├── bot_09_kelly_value.yaml
│   │   └── bot_10_longterm_value.yaml
│   │
│   ├── risk_management.yaml           # Global risk rules (circuit breakers, limits)
│   ├── zone_framework.yaml            # Zone 1-5 definitions and restrictions
│   ├── capital_allocation.yaml        # Capital distribution across bots
│   ├── api_endpoints.yaml             # Polymarket, news, esports API configs
│   ├── logging.yaml                   # Logging configuration (levels, handlers)
│   │
│   ├── prometheus/                    # Prometheus configuration
│   │   └── prometheus.yml             # Scrape configs, alerting rules
│   │
│   └── grafana/                       # Grafana dashboards (JSON)
│       ├── README.md                  # Dashboard import instructions
│       ├── bot_performance.json       # Bot ROI, Sharpe, drawdown
│       ├── system_health.json         # CPU, memory, latency, errors
│       ├── order_execution.json       # Success rate, slippage, fill times
│       └── risk_metrics.json          # Zone distribution, consecutive losses
│
├── src/                               # 🐍 Source Code
│   ├── __init__.py
│   │
│   ├── core/                          # Core Services (shared infrastructure)
│   │   ├── __init__.py
│   │   ├── websocket_gateway.py       # WebSocket connection manager
│   │   ├── market_data_processor.py   # Order book processing, spreads
│   │   ├── order_execution_engine.py  # Post-only orders, HMAC auth
│   │   ├── risk_manager.py            # Circuit breakers, Kelly, zone validator
│   │   ├── position_tracker.py        # Global position tracking
│   │   ├── event_bus.py               # Redis Pub/Sub event broadcasting
│   │   └── health_checker.py          # Service health monitoring
│   │
│   ├── bots/                          # Bot Implementations
│   │   ├── __init__.py
│   │   ├── base_bot.py                # Abstract base class (lifecycle, state)
│   │   ├── bot_manager.py             # Bot orchestrator (start/stop multiple)
│   │   ├── bot_01_market_rebalancing.py
│   │   ├── bot_02_esports_parsing.py
│   │   ├── bot_03_copy_trading.py
│   │   ├── bot_04_news_scalping.py
│   │   ├── bot_05_market_making.py
│   │   ├── bot_06_multi_outcome_arb.py
│   │   ├── bot_07_contrarian_attention.py
│   │   ├── bot_08_tail_risk_combo.py
│   │   ├── bot_09_kelly_value.py
│   │   └── bot_10_longterm_value.py
│   │
│   ├── strategies/                    # Strategy Logic (separated from bots)
│   │   ├── __init__.py
│   │   │
│   │   ├── arbitrage/                 # Arbitrage strategies
│   │   │   ├── __init__.py
│   │   │   ├── rebalancing_detector.py    # YES+NO≠$1 detection
│   │   │   ├── opportunity_scorer.py      # Score arb opportunities
│   │   │   └── multi_outcome_hedging.py   # Multi-outcome hedge calculator
│   │   │
│   │   ├── market_making/             # Market making components
│   │   │   ├── __init__.py
│   │   │   ├── spread_calculator.py       # Optimal spread sizing
│   │   │   ├── inventory_manager.py       # Inventory risk management
│   │   │   ├── volatility_filter.py       # Low volatility market filter
│   │   │   └── quote_engine.py            # Bid/ask quote generation
│   │   │
│   │   ├── event_driven/              # Event-driven strategies
│   │   │   ├── __init__.py
│   │   │   ├── esports_parser.py          # LoL/Dota2/VALORANT parsers
│   │   │   ├── news_aggregator.py         # Multi-source news aggregation
│   │   │   ├── sentiment_analyzer.py      # NLP sentiment analysis
│   │   │   └── event_validator.py         # Multi-source validation
│   │   │
│   │   ├── analytics/                 # Analytics & models
│   │   │   ├── __init__.py
│   │   │   ├── technical_indicators.py    # ADX, Bollinger, RSI (TA-Lib)
│   │   │   ├── probability_model.py       # Probability estimation
│   │   │   ├── kelly_calculator.py        # Half/Quarter Kelly sizing
│   │   │   ├── zone_classifier.py         # Zone 1-5 price classifier
│   │   │   └── sharpe_calculator.py       # Risk-adjusted returns
│   │   │
│   │   ├── copy_trading/              # Copy trading components
│   │   │   ├── __init__.py
│   │   │   ├── whale_monitor.py           # On-chain whale tracking
│   │   │   ├── signal_filter.py           # Profit/loss ratio filter
│   │   │   ├── leaderboard_tracker.py     # Top trader tracking
│   │   │   └── copy_ratio_calculator.py   # Position size calculator
│   │   │
│   │   └── tail_risk/                 # Tail risk strategies
│   │       ├── __init__.py
│   │       ├── low_liquidity_scanner.py   # Find illiquid markets
│   │       ├── tail_opportunity_filter.py # 0.1-5¢ opportunity filter
│   │       └── portfolio_diversifier.py   # 20-50 position diversifier
│   │
│   ├── data/                          # Data Access Layer
│   │   ├── __init__.py
│   │   ├── timescaledb.py             # TimescaleDB client (hypertables)
│   │   ├── redis_client.py            # Redis operations (cache, pub/sub)
│   │   ├── polymarket_api.py          # Polymarket CLOB/Gamma API wrapper
│   │   ├── polygon_rpc.py             # Polygon blockchain RPC client
│   │   ├── external_apis.py           # News, esports, sentiment APIs
│   │   └── models.py                  # SQLAlchemy + Pydantic schemas
│   │
│   ├── dashboard/                     # 📊 Streamlit Dashboard
│   │   ├── __init__.py
│   │   ├── app.py                     # Main Streamlit entry point
│   │   │
│   │   ├── pages/                     # Multi-page dashboard
│   │   │   ├── 1_🏠_Overview.py       # Main overview page
│   │   │   ├── 2_🤖_Bot_Control.py    # Individual bot controls
│   │   │   ├── 3_📈_Performance.py    # Performance analytics
│   │   │   ├── 4_💰_Positions.py      # Active positions
│   │   │   ├── 5_📜_Order_Log.py      # Order execution history
│   │   │   ├── 6_⚠️_Risk_Monitor.py   # Risk metrics, circuit breakers
│   │   │   └── 7_⚙️_Settings.py       # Configuration management
│   │   │
│   │   ├── components/                # Reusable dashboard components
│   │   │   ├── __init__.py
│   │   │   ├── control_panel.py       # Start/stop/emergency halt
│   │   │   ├── metrics_cards.py       # ROI, Sharpe, drawdown cards
│   │   │   ├── pnl_chart.py           # Real-time P&L chart
│   │   │   ├── position_table.py      # Active positions table
│   │   │   ├── order_log_table.py     # Order history table
│   │   │   ├── zone_heatmap.py        # Zone distribution heatmap
│   │   │   ├── latency_monitor.py     # WebSocket/API latency
│   │   │   ├── circuit_breaker_status.py  # Circuit breaker indicators
│   │   │   └── bot_status_grid.py     # Bot status grid (running/stopped)
│   │   │
│   │   └── utils/                     # Dashboard utilities
│   │       ├── __init__.py
│   │       ├── websocket_client.py    # WebSocket client for updates
│   │       ├── api_client.py          # Internal API client
│   │       ├── theme.py               # Dark minimalist theme
│   │       ├── formatters.py          # Number/date formatters
│   │       └── session_state.py       # Streamlit session management
│   │
│   ├── api/                           # 🌐 Internal FastAPI REST API
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry point
│   │   │
│   │   ├── routes/                    # API routes
│   │   │   ├── __init__.py
│   │   │   ├── bots.py                # Bot control endpoints
│   │   │   ├── positions.py           # Position management
│   │   │   ├── orders.py              # Order history/management
│   │   │   ├── metrics.py             # Metrics (Prometheus format)
│   │   │   ├── health.py              # Health check endpoints
│   │   │   ├── risk.py                # Risk management endpoints
│   │   │   └── config.py              # Configuration endpoints
│   │   │
│   │   ├── middleware/                # API middleware
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                # API key authentication
│   │   │   ├── rate_limiter.py        # Rate limiting
│   │   │   ├── cors.py                # CORS configuration
│   │   │   └── error_handler.py       # Global error handling
│   │   │
│   │   └── schemas/                   # Pydantic request/response schemas
│   │       ├── __init__.py
│   │       ├── bot_schemas.py
│   │       ├── position_schemas.py
│   │       ├── order_schemas.py
│   │       └── metric_schemas.py
│   │
│   ├── monitoring/                    # 📡 Monitoring & Observability
│   │   ├── __init__.py
│   │   ├── prometheus_exporter.py     # Custom Prometheus metrics
│   │   ├── metrics_collector.py       # Collect bot/system metrics
│   │   ├── alerts.py                  # Telegram/Discord alerts
│   │   ├── logger.py                  # Structured JSON logging
│   │   └── profiler.py                # Performance profiling
│   │
│   └── utils/                         # 🔧 Shared Utilities
│       ├── __init__.py
│       ├── config_loader.py           # YAML config loader/validator
│       ├── crypto.py                  # HMAC-SHA256, wallet operations
│       ├── datetime_utils.py          # Timezone-aware helpers
│       ├── retry.py                   # Exponential backoff decorator
│       ├── validators.py              # Input validation helpers
│       ├── constants.py               # System-wide constants
│       └── exceptions.py              # Custom exception classes
│
├── tests/                             # 🧪 Test Suite
│   ├── __init__.py
│   ├── conftest.py                    # Pytest fixtures (DB, Redis, mocks)
│   │
│   ├── unit/                          # Unit tests (isolated)
│   │   ├── __init__.py
│   │   ├── test_risk_manager.py
│   │   ├── test_zone_classifier.py
│   │   ├── test_kelly_calculator.py
│   │   ├── test_order_execution.py
│   │   ├── test_spread_calculator.py
│   │   └── test_rebalancing_detector.py
│   │
│   ├── integration/                   # Integration tests (multi-component)
│   │   ├── __init__.py
│   │   ├── test_websocket_gateway.py
│   │   ├── test_timescaledb.py
│   │   ├── test_redis_pubsub.py
│   │   └── test_api_endpoints.py
│   │
│   ├── e2e/                           # End-to-end tests (full flow)
│   │   ├── __init__.py
│   │   ├── test_bot_lifecycle.py      # Start → trade → stop
│   │   ├── test_emergency_halt.py     # Emergency stop all bots
│   │   └── test_paper_trading.py      # Paper trading mode
│   │
│   └── fixtures/                      # Test data fixtures
│       ├── orderbook_snapshots.json
│       ├── market_data.json
│       └── trade_history.json
│
├── scripts/                           # 🛠️ Utility Scripts
│   ├── setup_db.py                    # Initialize TimescaleDB hypertables
│   ├── seed_db.py                     # Seed database with test data
│   ├── migrate_data.py                # Data migration scripts
│   ├── backtest.py                    # Backtesting framework
│   ├── paper_trade.py                 # Paper trading mode launcher
│   ├── health_check.py                # System health check
│   ├── backup_db.sh                   # Database backup script
│   ├── restore_db.sh                  # Database restore script
│   ├── clean_logs.sh                  # Clean old log files
│   └── deploy_vps.sh                  # Deploy to VPS script
│
├── infra/                             # 🏗️ Infrastructure as Code
│   │
│   ├── docker/                        # Docker configurations
│   │   ├── Dockerfile.base            # Base image (shared dependencies)
│   │   ├── Dockerfile.core            # Core services image
│   │   ├── Dockerfile.bots            # Bots image
│   │   ├── Dockerfile.dashboard       # Dashboard image
│   │   ├── Dockerfile.api             # API image
│   │   └── .dockerignore              # Docker build exclusions
│   │
│   ├── kubernetes/                    # K8s manifests (future scaling)
│   │   ├── README.md
│   │   ├── namespace.yaml
│   │   ├── configmaps/
│   │   ├── secrets/
│   │   ├── deployments/
│   │   ├── services/
│   │   ├── ingress.yaml
│   │   └── monitoring/
│   │
│   └── terraform/                     # Terraform (VPS provisioning)
│       ├── README.md
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── modules/
│           ├── vpc/
│           ├── compute/
│           └── storage/
│
├── data/                              # 💾 Data Directory (mounted volumes)
│   ├── .gitkeep                       # Keep directory in git
│   ├── timescaledb/                   # PostgreSQL data (Docker volume)
│   ├── redis/                         # Redis persistence (Docker volume)
│   ├── logs/                          # Application logs
│   │   ├── core/
│   │   ├── bots/
│   │   ├── api/
│   │   └── dashboard/
│   ├── backups/                       # Database backups
│   └── exports/                       # Data exports (CSV, JSON)
│
├── notebooks/                         # 📓 Jupyter Notebooks
│   ├── README.md
│   ├── 01_strategy_backtest.ipynb     # Strategy backtesting
│   ├── 02_performance_analysis.ipynb  # P&L, Sharpe analysis
│   ├── 03_market_research.ipynb       # Market opportunity research
│   ├── 04_risk_analysis.ipynb         # Risk metrics analysis
│   └── 05_data_exploration.ipynb      # TimescaleDB data exploration
│
└── .github/                           # 🤖 GitHub-specific Files
    ├── workflows/                     # GitHub Actions CI/CD
    │   ├── ci.yml                     # CI: lint, test, build
    │   ├── cd.yml                     # CD: deploy to VPS
    │   ├── docker-publish.yml         # Publish Docker images
    │   ├── test.yml                   # Run test suite
    │   └── security-scan.yml          # Security vulnerability scan
    │
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   ├── feature_request.md
    │   └── strategy_proposal.md
    │
    ├── PULL_REQUEST_TEMPLATE.md
    └── CODEOWNERS                     # Code ownership
```

## Key Design Principles

### 1. Separation of Concerns
- **core/**: Shared infrastructure services
- **bots/**: Orchestration logic only
- **strategies/**: Pure strategy logic (reusable, testable)
- **data/**: Single source for data access

### 2. Modularity
- Each bot can run independently
- Strategies are reusable across bots
- Core services are shared to avoid duplication

### 3. Configuration Management
- All configs externalized to `config/`
- Per-bot YAML configs
- Environment-specific overrides (dev/test/prod)

### 4. Observability First
- Structured JSON logging
- Prometheus metrics built-in
- Grafana dashboards pre-configured
- Health check endpoints

### 5. Testing Strategy
- Unit tests: Isolated component testing
- Integration tests: Multi-component flows
- E2E tests: Complete bot lifecycle
- Fixtures for reproducible tests

### 6. Docker-First Development
- All services containerized
- Docker Compose for orchestration
- Hot-reload in development
- Production-ready images

### 7. Documentation Co-Located
- Architecture docs in `docs/`
- API docs auto-generated (FastAPI)
- README in each major directory
- Inline code documentation

## File Count Summary

- **Total Directories**: ~50
- **Total Files**: ~150
- **Python Modules**: ~80
- **Config Files**: ~20
- **Docker Files**: ~7
- **Documentation**: ~15
- **Tests**: ~20
- **Scripts**: ~10

## Next Steps

1. ✅ Directory structure defined
2. ⏭️ Generate core configuration files
3. ⏭️ Create README.md with setup instructions
4. ⏭️ Generate .gitignore optimized for this project
5. ⏭️ Create docker-compose.yml orchestration
6. ⏭️ Generate Makefile with common commands
