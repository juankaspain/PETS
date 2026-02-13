# 🚀 PETS - Polymarket Elite Trading System

## 📋 Contexto del Proyecto

**Nombre**: Polymarket Elite Trading System (PETS)  
**Repositorio**: https://github.com/juankaspain/PETS  
**Objetivo**: Sistema institucional de 10 bots de trading para Polymarket, operando en el 0.04% elite que captura 70% de profits totales  
**Uso**: Personal, alta disponibilidad, production-grade desde día 1  

### Stack Tecnológico

```
Backend:     Python 3.11+, asyncio, type hints
Database:    TimescaleDB (PostgreSQL + hypertables), Redis 7.2
API:         FastAPI 0.108 (/api/v1/)
Dashboard:   Streamlit 1.30+ (real-time WebSocket)
Blockchain:  Web3.py (Polygon), eth_account
Monitoring:  Prometheus, Grafana
Infra:       Docker Compose (16 services)
Testing:     pytest, pytest-cov, testcontainers
Linting:     black, ruff, mypy --strict
```

---

## 🏗️ Arquitectura (Clean Architecture + DDD + Hexagonal)

### Dependency Rule
**ESTRICTA**: Inner layers NUNCA conocen outer layers. Dependencies apuntan hacia el centro (domain).

### Capa 1: Domain Layer (`src/domain/`)
**Responsabilidad**: Core business logic, reglas de negocio, entidades puras

#### Entities (`src/domain/entities/`)
- `Bot`: bot_id, strategy_type, state, config, capital_allocated, created_at
- `Order`: order_id, bot_id, market_id, side, size, price, zone, status, timestamp
- `Position`: position_id, bot_id, order_id, market_id, side, entry_price, current_price, pnl, zone, opened_at
- `Market`: market_id, question, outcomes, liquidity, volume, created_at, resolves_at
- `Trade`: trade_id, order_id, executed_price, executed_size, fees_paid, slippage, timestamp
- `Wallet`: address, balance_usdc, balance_matic, nonce, last_sync_at

#### Value Objects (`src/domain/value_objects/`)
- `Price(value: Decimal, zone: int)`: Immutable, validates 0.01-0.99, auto-classifies zone
- `Quantity(value: Decimal, decimals: int)`: Immutable, validates >0
- `OrderId(value: str)`: NewType, validates UUID format
- `MarketId(value: str)`: NewType, validates hex format
- `Side(Enum)`: YES, NO
- `OrderStatus(Enum)`: PENDING, FILLED, PARTIALLY_FILLED, CANCELED, REJECTED, EXPIRED
- `BotState(Enum)`: IDLE, STARTING, ACTIVE, PAUSED, STOPPING, STOPPED, ERROR, EMERGENCY_HALT
- `Zone(Enum)`: ZONE_1, ZONE_2, ZONE_3, ZONE_4, ZONE_5

#### Domain Services (`src/domain/services/`)
- `RiskCalculator`: calculate_position_risk, validate_order_risk, check_drawdown
- `KellyCalculator`: calculate_kelly_fraction (Half/Quarter), validate_edge
- `ZoneClassifier`: classify_price_zone, validate_zone_restrictions
- `PnLCalculator`: calculate_realized_pnl, calculate_unrealized_pnl, calculate_sharpe_ratio
- `FeeCalculator`: calculate_taker_fee (0-3.15%), calculate_maker_rebate (20%)
- `GasEstimator`: estimate_gas_limit, calculate_gas_cost_usdc, optimize_gas_price

#### Domain Events (`src/domain/events/`)
- `OrderPlacedEvent(order_id, bot_id, market_id, timestamp)`
- `PositionOpenedEvent(position_id, bot_id, size, entry_price, zone)`
- `PositionClosedEvent(position_id, realized_pnl, hold_duration)`
- `CircuitBreakerTriggeredEvent(bot_id, reason, threshold_value, current_value)`
- `EmergencyHaltEvent(trigger_reason, affected_bots, timestamp)`
- `DrawdownThresholdEvent(bot_id, current_drawdown, threshold)`
- `WalletBalanceLowEvent(wallet_address, balance_usdc, threshold)`
- `GasSpikeDetectedEvent(current_gwei, threshold_gwei, action)`

#### Repository Protocols (`src/domain/repositories/`)
- `BotRepository(Protocol)`: save, find_by_id, find_active, update_state
- `OrderRepository(Protocol)`: save, find_by_id, find_by_bot_id, update_status
- `PositionRepository(Protocol)`: save, find_open_by_bot, close_position
- `MarketRepository(Protocol)`: find_by_id, find_active, update_liquidity
- `WalletRepository(Protocol)`: get_balance, update_balance, get_nonce

#### Domain Exceptions (`src/domain/exceptions/`)
```
PETSError (base)
├── DomainError
│   ├── OrderError
│   │   ├── InvalidOrderError
│   │   ├── InsufficientBalanceError
│   │   ├── OrderRejectedError
│   │   └── DuplicateOrderError
│   ├── PositionError
│   │   ├── PositionNotFoundError
│   │   └── PositionAlreadyClosedError
│   ├── RiskViolation
│   │   ├── ZoneViolationError
│   │   ├── DrawdownExceededError
│   │   ├── ExposureLimitError
│   │   └── ConsecutiveLossesError
│   ├── WalletError
│   │   ├── InsufficientGasError
│   │   ├── InsufficientUSDCError
│   │   ├── NonceOutOfSyncError
│   │   └── WalletLockedError
│   └── CircuitBreakerOpenError
├── InfrastructureError
└── ApplicationError
```

---

### Capa 2: Application Layer (`src/application/`)
**Responsabilidad**: Use cases, orquestación, DTOs. Stateless, sin business logic.

#### Use Cases (`src/application/use_cases/`)
- `PlaceOrderUseCase`: Coordina validación risk + ejecución order + publish event
- `OpenPositionUseCase`: Valida wallet balance + abre position + actualiza DB
- `ClosePositionUseCase`: Cierra position + calcula P&L + emite event
- `CalculateRiskUseCase`: Valida order contra risk rules (zones, drawdown, exposure)
- `ExecuteBotStrategyUseCase`: Ejecuta ciclo bot + genera orders + valida risk
- `EmergencyHaltUseCase`: Detiene todos bots + cierra posiciones + alert
- `TopUpWalletUseCase`: Transfer funds cold → hot wallet
- `RebalanceWalletUseCase`: Auto-rebalance hot wallet si balance <threshold
- `ValidateZoneRestrictionUseCase`: Valida si order cumple zone restrictions
- `CalculateKellySizeUseCase`: Calcula position size óptimo (Half/Quarter Kelly)

#### DTOs (`src/application/dtos/`)
- `OrderDTO`: market_id, side, size, price, bot_id, strategy_type, post_only
- `PositionDTO`: bot_id, market_id, side, size, entry_price, stop_loss, take_profit
- `MarketDataDTO`: market_id, yes_price, no_price, liquidity, volume_24h, last_update
- `RiskMetricsDTO`: bot_id, current_drawdown, consecutive_losses, open_exposure
- `WalletBalanceDTO`: address, usdc_balance, matic_balance, pending_transactions

#### Application Services (`src/application/services/`)
- `TransactionCoordinator`: Coordina múltiples use cases en transacción
- `EventPublisher`: Publica domain events al event bus
- `CacheInvalidator`: Invalida caches cuando domain events ocurren

#### Paper Trading (`src/application/paper_trading/`)

**PaperTradingEngine** (`paper_trading_engine.py`):
- Virtual balance management: Initial $5K, available/reserved tracking
- Simulated order execution: POST_ONLY 70% fill probability, MARKET/LIMIT instant
- Realistic slippage: 0.1% average, 0.5% max, based on market conditions
- Fee simulation: Polymarket 2% taker, 0% maker
- Latency simulation: Configurable delay (default 50ms)
- P&L tracking: Realized/unrealized separation
- Position management: Open/close virtual positions
- Performance metrics: ROI, win rate, Sharpe ratio estimation
- State reset: Clean reset to initial state
- Safety: No real wallet interaction, no blockchain transactions

**Paper Trading Use Cases**:
- `RunPaperTradingUseCase`: Orchestrates complete session (duration, strategy execution, performance summary)
- `GetPaperTradingStatsUseCase`: Real-time metrics (balance, positions, P&L, ROI)
- `ResetPaperTradingUseCase`: Clean state reset with audit trail

**Features**:
- VirtualBalance: available/reserved/total tracking
- VirtualPosition: unrealized P&L calculation, value tracking
- Order simulation: POST_ONLY requires price improvement, MARKET fills immediately
- Partial fills: Realistic fragmentation modeling
- Slippage model: Random within bounds, side-dependent (pay more YES, receive less NO)
- Fee calculation: Maker/taker distinction, accumulation tracking
- Performance summary: initial_balance, current_balance, portfolio_value, realized_pnl, unrealized_pnl, total_pnl, total_fees, open_positions, roi

---

### Capa 3: Infrastructure Layer (`src/infrastructure/`)
**Responsabilidad**: Integraciones externas, persistencia, implementaciones concretas.

#### Repositories (`src/infrastructure/repositories/`)
- `TimescaleDBOrderRepository`: Implementa OrderRepository con asyncpg
- `TimescaleDBPositionRepository`: Implementa PositionRepository con hypertables
- `RedisPositionRepository`: Cache hot data positions (TTL 30s)
- `TimescaleDBMarketRepository`: Implementa MarketRepository
- `RedisWalletRepository`: Cache wallet state con Redis locks

#### External Services (`src/infrastructure/external/`)
- `PolymarketCLOBClient`: HTTP client HMAC-SHA256 auth, rate limit 3500/10s burst
- `PolymarketWebSocketClient`: Persistent WebSocket auto-reconnect, heartbeat
- `PolygonRPCClient`: Web3.py wrapper, connection pooling, nonce management
- `NewsAPIClient`: Multi-source (NewsAPI, Bloomberg, Reuters RSS)
- `EsportsAPIClient`: Riot Games, Steam, Abios, PandaScore
- `KaitoAPIClient`: Attention markets + social sentiment

#### Persistence (`src/infrastructure/persistence/`)

**SQLAlchemy Models**:
- BotModel, OrderModel, PositionModel, TradeModel, MarketModel, WalletModel
- Migrations: Alembic timestamped, reversible

**Redis Schemas**:
- OrderBookSchema, PositionSnapshotSchema, WalletStateSchema
- JSON serialization + gzip (si payload >1KB)

**TimescaleDB Hypertables**:
- `orders`: partitioned by timestamp, 7-day chunks
- `positions`: partitioned by timestamp, 7-day chunks
- `trades`: partitioned by timestamp, 7-day chunks
- `market_snapshots`: partitioned by timestamp, 1-day chunks

#### Messaging (`src/infrastructure/messaging/`)
**RedisPubSubEventBus**:
- Channels: `orderbook.{market_id}`, `trades.{bot_id}`, `events.{event_type}`
- Delivery: At-least-once guarantee
- Consumer groups: Multiple consumers per channel

#### Wallet Management (`src/infrastructure/wallet/`)

**WalletManager** (`wallet_manager.py`):
- Hot wallet: 10-20% capital, auto-rebalance si <5%
- Cold wallet: 80-90% capital, manual access
- Nonce tracking: Redis locks, thread-safe
- Transaction signing: Local (eth_account), NUNCA enviar private key
- Methods: get_balance, auto_rebalance, sign_transaction, submit_transaction

**GasManager** (`gas_manager.py`):
- Monitor: Polygon Gas Station API (refresh 10s)
- Adaptive: rapid <30gwei, fast 30-50, standard 50-100, queue >100
- EIP-1559: maxPriorityFeePerGas 30, maxFeePerGas base+30
- Tracking: gas_cost_usdc por bot para ROI calculation

**NonceManager** (`nonce_manager.py`):
- Redis key: `nonce:{address}` con Redis lock 5s TTL
- Sync blockchain: startup + every 5min + on error
- Prevent collisions múltiples bots mismo wallet

**WalletRecovery** (`wallet_recovery.py`):
- BIP39 mnemonic 24-word encrypted AES-256
- Emergency withdrawal: transfer ALL to cold wallet
- Wallet rotation: cambiar hot wallet sin downtime

**WalletMonitor** (`wallet_monitor.py`):
- Balance alerts: USDC <$2.5K warning, <$1K critical
- Tx monitoring: bump gas 10% si pending >2min
- Stuck detection: manual intervention si >10min pending

**Security Best Practices**:
- ✅ NUNCA log private keys (ni debug)
- ✅ NUNCA send private keys over network
- ✅ Encrypt at rest AES-256
- ✅ Env vars para secrets
- ✅ Rotate wallets 90d
- ✅ Rate limit operations
- ✅ Audit trail ALL transactions

---

### Capa 4: Presentation Layer (`src/presentation/`)
**Responsabilidad**: User interfaces (API, Dashboard).

#### API (`src/presentation/api/`)

**FastAPI** (`/api/v1/`), **17 routes**:
- `/bots`: GET list, GET /{id}, POST /{id}/start, POST /{id}/stop, POST /{id}/pause, PUT /{id}/config
- `/positions`: GET list, GET /{id}, POST /{id}/close
- `/orders`: GET list, GET /{id}, POST place, DELETE /{id}
- `/metrics`: GET /bots/{id}, GET /portfolio, GET /prometheus
- `/health`: GET /live, GET /ready, GET /startup
- `/wallet`: GET /balance, POST /topup, POST /rebalance, GET /transactions
- `/risk`: GET /metrics, GET /circuit-breakers, POST /emergency-halt

**Middleware**:
- `AuthMiddleware`: API key validation (X-API-Key header)
- `RateLimitMiddleware`: 100 req/min per client (Redis-backed)
- `CORSMiddleware`: Allow dashboard origin
- `RequestIDMiddleware`: correlation_id para tracing
- `LoggingMiddleware`: JSON structured requests/responses
- `ErrorHandlerMiddleware`: Consistent error format

#### Dashboard (`src/presentation/dashboard/`) ✅

**Streamlit multi-page app**, **7 páginas IMPLEMENTADAS**:

**1. 🏠 Overview** (`pages/1_Overview.py`):
- Emergency controls: HALT ALL, PAUSE ALL, RESUME ALL (prominent placement)
- Metrics cards grid: Portfolio Value, Total P&L, Open Positions, Active Bots (1s updates)
- P&L chart: Real-time cumulative P&L line chart
- Portfolio composition: Pie chart by bot allocation
- Zone heatmap: Exposure distribution across 5 zones
- Bot status grid: Quick view all 10 bots
- Auto-refresh: 1s WebSocket updates
- Features: Interactive Plotly charts, color-coded status, session state persistence

**2. 🤖 Bot Control** (`pages/2_Bot_Control.py`):
- Bot status grid: All 10 bots with state indicators (IDLE/STARTING/ACTIVE/PAUSED/STOPPED/ERROR)
- Bot detail panel:
  - Real-time metrics: P&L, positions, win rate, Sharpe ratio (2s updates)
  - Performance charts: ROI trend line, position history bar chart
  - Config editor: YAML inline editing with validation
  - Action buttons: START, STOP, PAUSE, RESUME, EMERGENCY HALT (confirmation dialogs)
  - Live logs: Last 50 entries with filtering by level (INFO/WARNING/ERROR)
- State diagram: Visual bot lifecycle (IDLE → STARTING → ACTIVE ⇄ PAUSED → STOPPING → STOPPED/ERROR)
- Auto-refresh: 2s WebSocket updates
- Features: Interactive bot selection, config hot-reload validation, graceful error handling

**3. 📈 Performance** (`pages/3_Performance.py`):
- Comparative table: All bots side-by-side
  - Columns: Bot ID, Strategy, ROI, P&L, Win Rate, Sharpe, Positions, Status
  - Sortable by any metric
  - Color-coded performance tiers (Elite/Good/Average/Poor badges)
- ROI chart: Multi-line chart all bots over time (Plotly interactive)
- Risk-adjusted scatter: Sharpe vs ROI positioning (bubble size = P&L)
- Drawdown analysis: Max drawdown per bot with threshold lines (25% bot, 40% portfolio)
- Trade distributions:
  - Histogram: P&L distribution per bot
  - Box plot: Position hold times
- Filtering: By strategy type, status, date range
- Export: CSV download capability
- Features: Interactive charts, color-coded tiers, responsive layouts

**4. 💰 Positions** (`pages/4_Positions.py`):
- Active positions table: Real-time 1s updates
  - Columns: Bot, Market, Side, Size, Entry, Current, P&L, Duration, Zone, Status
  - Color-coded: GREEN profit, RED loss, GRAY neutral
  - Sortable by P&L, duration, size
- Position detail modal:
  - Entry/exit info: prices, timestamps, fees
  - P&L breakdown: realized/unrealized split
  - Market context: current prices, liquidity
  - Action button: CLOSE POSITION (confirmation dialog)
- Closed positions history:
  - Last 100 closed positions
  - Filterable: bot_id, date range, profit/loss
  - Metrics: Total P&L, avg hold time, win rate
- Position heatmap: Bubble chart (size vs P&L with zone colors)
- Portfolio value chart: Time series with realized vs unrealized P&L stacked area
- Auto-refresh: 1s WebSocket updates
- Export: CSV download active/closed positions

**5. 📜 Order Log** (`pages/5_Order_Log.py`):
- Execution table: 2s updates
  - Columns: Time, Bot, Market, Side, Type, Size, Price, Status, Fill%, Latency
  - Status badges: FILLED (green), PARTIAL (yellow), CANCELED (gray), REJECTED (red)
  - Sortable by time, latency, fill rate
- Order detail modal:
  - Execution timeline: submitted → acknowledged → filled
  - Fill breakdown: partial fills history
  - Rejection reason (if applicable)
  - Gas cost + slippage details
- Filters:
  - Bot selection dropdown
  - Status checkboxes (all/filled/pending/canceled)
  - Time range picker (last 1h/6h/24h/7d)
  - Order type filter (POST_ONLY/MARKET/LIMIT)
- Performance metrics cards:
  - Fill rate: percentage orders filled
  - Avg latency: submission to ack time
  - Rejection rate: percentage rejected
  - Total volume: 24h USDC traded
- Latency distribution: Histogram with 100ms p99 target line
- Rejection analysis: Pie chart reasons breakdown + bar chart per bot
- Trade size distribution: Histogram order sizes grouped
- Export: CSV download order log

**6. ⚠️ Risk Monitor** (`pages/6_Risk_Monitor.py`):
- Zone exposure grid:
  - 5 zones visual representation
  - Current exposure % per zone
  - Limit thresholds with progress bars
  - Color-coded: GREEN safe, YELLOW warning, RED danger
- Circuit breaker status:
  - All 4 circuit breakers real-time
  - Status: ARMED/TRIGGERED with timestamps
  - Threshold tracking: consecutive losses, daily loss, bot drawdown, portfolio drawdown
  - Auto-reset countdown timers
- Drawdown gauges:
  - Portfolio drawdown: current vs 40% emergency threshold
  - Bot-specific drawdowns: individual 25% thresholds
  - Color-coded gauge charts (Plotly)
- Consecutive loss tracker:
  - Per-bot consecutive loss count
  - 3-loss threshold visualization
  - Recent losses timeline
- Risk alerts feed:
  - Real-time WebSocket alerts stream
  - Last 50 alerts scrollable
  - Alert types: ZONE_VIOLATION, CIRCUIT_BREAKER, DRAWDOWN_WARNING
  - Filterable by severity (INFO/WARNING/CRITICAL)
- Zone heatmap: Interactive exposure concentration (click to drill-down by bot)
- Auto-refresh: 1s updates

**7. ⚙️ Settings** (`pages/7_Settings.py`):
- 5 tabs organized structure:

  **Tab 1 - Global Config:**
  - Emergency controls: HALT ALL, PAUSE ALL, RESUME ALL
  - Risk parameters: Max portfolio drawdown (40% default), Max daily loss % (5% default), Circuit breaker thresholds
  - Trading parameters: Default order type (POST_ONLY), Max slippage tolerance (0.5%), Rate limit settings
  - Save button with validation

  **Tab 2 - Bot-Specific:**
  - Bot selector dropdown (Bot 1-10)
  - Per-bot config editor: Capital allocation ($), Kelly fraction (Half/Quarter/Full), Max position size, Zone restrictions, Strategy-specific params (YAML inline)
  - Enable/disable individual bots
  - Reset to defaults button

  **Tab 3 - Notifications:**
  - Alert channels: Email notifications (SMTP config), Webhook URLs (Slack/Discord), SMS alerts (Twilio config)
  - Alert thresholds: Circuit breaker triggers, Balance warnings, Performance alerts
  - Test notification button

  **Tab 4 - Database:**
  - Connection status: TimescaleDB + Redis
  - Performance metrics: Query latency p50/p99, Connection pool usage, Cache hit rate
  - Maintenance: Compression status, Retention policy info, Backup status (last backup timestamp)
  - Actions: Run compression now, Clear Redis cache, Export database snapshot

  **Tab 5 - System Health:**
  - Service status grid: API (FastAPI), Dashboard (Streamlit), Database (TimescaleDB), Cache (Redis), WebSocket gateway, All 10 bots
  - Resource usage: CPU % per service, Memory MB per service, Network I/O
  - Logs viewer: Last 100 log entries, Filter by service/level, Live tail option
  - System actions: Restart service buttons, Clear logs, Download diagnostics

**Components Library** (`src/presentation/dashboard/components/`):
- `metric_card.py`: Reusable metric display cards with color coding
- `chart_utils.py`: Common Plotly chart configurations and themes
- `websocket_client.py`: Real-time WebSocket connection with auto-reconnect
- `api_client.py`: Backend API HTTP client with retry logic
- `state_manager.py`: Session state management and persistence

**Integration**:
- FastAPI backend: /api/v1/metrics, /api/v1/bots, /api/v1/positions, /api/v1/orders, /api/v1/risk, /api/v1/config
- WebSocket: /ws/bots/status, /ws/positions/{bot_id}, /ws/risk/alerts (real-time updates)
- Authentication: API key header (X-API-Key)

**Production-Ready Features**:
- Input validation all forms (Pydantic)
- Confirmation dialogs destructive actions (HALT, CLOSE, DELETE)
- Loading spinners async operations
- Error messages user-friendly
- Graceful degradation if backend unavailable
- Auto-reconnect WebSocket on disconnect
- Session state persistence across page navigation
- Type hints mypy strict
- Docstrings Google style comprehensive
- Responsive layouts mobile/tablet/desktop
- Color-coded status indicators (green/yellow/red)
- Performance tier badges (Elite/Good/Average/Poor)
- Audit trail all config changes
- Rollback capability config changes

---

### Bots Layer (`src/bots/`)

**BaseBotStrategy** (ABC):
- Abstract: initialize, execute_cycle, stop_gracefully, get_state, get_metrics
- Implemented: start, pause, resume, stop, emergency_halt
- State machine: IDLE → STARTING → ACTIVE ⇄ PAUSED → STOPPING → STOPPED/ERROR

**Concrete Bots** (8/10 implementados):

**Bot 1 - Rebalancing** (`bot_01_rebalancing.py`) ✅:
- Paired markets arbitrage (Trump Yes vs Trump No)
- Drift detection: 0.5% threshold
- Simultaneous opposite orders
- Zone 2-3 balanced focus
- Half Kelly sizing
- Target: 0.3-0.8% per trade

**Bot 2 - Esports** (`bot_02_esports.py`) ✅:
- Live betting: LoL, CS2, Dota 2
- WebSocket game state monitoring
- Momentum detection: 5-kill swing, 2-tower advantage
- Zone 2-3 high-volume focus
- 5-15min pre-event entry window
- Quarter Kelly conservative

**Bot 3 - Copy Trading** (`bot_03_copy_trading.py`) ✅:
- Track top 20 traders (>60% win rate)
- Copy timing: within 30s detection
- Position sizing: 20-50% of original
- Zone 1-3 restriction (avoid extremes)
- Risk per trade: max 2%
- Stop copy if trader <55% win rate

**Bot 4 - News-driven** (`bot_04_news_driven.py`) ✅:
- Multi-source: NewsAPI, Bloomberg, Reuters, Twitter
- NLP sentiment: positive/negative/neutral classification
- Speed: <5s from news to order
- Zone 1-2 early mover advantage
- Position size based on sentiment confidence
- Hold period: 2-12h event impact window

**Bot 5 - Market Making** (`bot_05_market_maker.py`) ✅:
- Spread optimization: 0.5-2% dynamic
- Inventory management: max 30% skew
- Zone 2-3 balanced markets focus
- WebSocket orderbook real-time
- Half Kelly sizing
- Target: 0.2-0.5% per fill, 40-80 fills/day

**Bot 6 - Multi-outcome** (`bot_06_multi_outcome.py`) ✅:
- Correlation analysis between outcomes
- Portfolio optimization across linked markets
- Hedging: 30% hedge ratio target
- Max 40% exposure per outcome
- Zone 2-3 balanced focus
- Min 0.50 correlation detection
- Up to 12 simultaneous positions
- Quarter Kelly sizing

**Bot 7 - Contrarian** (`bot_07_contrarian.py`) ✅:
- RSI momentum detection (14 period)
- Overbought >75, Oversold <25
- Mean reversion: 24h window, 2 std dev extremes
- Fade crowded positions (max crowd score 80)
- Zone 1-2 extreme value focus
- 12h hold period for reversion
- 20% Kelly (conservative)
- 25% drawdown tolerance

**Bot 8 - Tail Risk** (`bot_08_tail_risk_combo.py`) ✅:
- Low liquidity scanner (<$1K)
- Multi-strategy: Tail Risk + Adaptive MM
- Zone 1-2 extreme value focus
- Quarter Kelly conservative
- Evidence: $106K planktonXD profits
- Target: 8-12% monthly returns
- Max drawdown: 15%

**Bot 9 - Kelly Optimizer** (pendiente):
- Dynamic Kelly fraction adjustment
- Win rate tracking
- Edge recalculation

**Bot 10 - Long-term Value** (pendiente):
- Macro markets (>90 days)
- Fundamental analysis
- Zone 1-2 mispricing focus

**BotOrchestrator**: Lifecycle management, dependency injection, emergency halt all

**BotFactory**: create(bot_id, config) → BaseBotStrategy

---

## 💾 Database Optimization (TimescaleDB)

### Hypertables

**orders** (7-day chunks):
- Indices: (bot_id, created_at DESC), (market_id, created_at DESC), (status, created_at DESC), (zone, created_at DESC)
- Compression: 14d policy, 4-5x ratio
- Retention: 365d

**positions** (7-day chunks):
- Indices: (bot_id, opened_at DESC) WHERE closed_at IS NULL, (bot_id, closed_at DESC) WHERE closed_at IS NOT NULL
- Compression: 14d policy, 3.8x ratio
- Retention: 365d

**trades** (7-day chunks):
- Indices: (bot_id, executed_at DESC), (order_id, executed_at DESC)
- Compression: 14d policy, 4.5x ratio
- Retention: 365d

**market_snapshots** (1-day chunks):
- Indices: (market_id, snapshot_at DESC)
- Compression: 7d policy
- Retention: 90d

### Continuous Aggregates

**bot_performance_hourly**: trades_count, volume_usdc, fees, gas_cost, avg_slippage por hora
**bot_pnl_daily**: positions_closed, total_pnl, avg_pnl, win_rate por día
**market_price_5min**: OHLC por 5 minutos

### Performance Targets

- Simple queries: **<10ms p99**
- Aggregations: **<50ms p99**
- Dashboard: **<100ms p99**
- Writes: **<10ms p99**

---

## 🔒 Risk Management

### Framework 5-Zones

| Zone | Range | Directional | Restriction |
|------|-------|-------------|-------------|
| Z1 | 0.05-0.20 | ✅ OK | Tail risk, contrarian |
| Z2 | 0.20-0.40 | ✅ OK | Value betting |
| Z3 | 0.40-0.60 | ⚠️ Edge required | Arb/MM solo |
| Z4 | 0.60-0.80 | ❌ PROHIBIDO | Arb/MM solo |
| Z5 | 0.80-0.98 | ❌ PROHIBIDO | Arb/MM solo |

### Circuit Breakers

1. **3 consecutive losses** → Pause bot 24h
2. **5% daily loss** → Halt all bots
3. **25% bot drawdown** → Halt specific bot
4. **40% portfolio drawdown** → Emergency halt ALL

### Kelly Criterion

- **PROHIBIDO**: Full Kelly
- **OBLIGATORIO**: Half Kelly
- **CONSERVADOR**: Quarter Kelly

Formula Half Kelly: `f* = (bp - q) / b / 2`

### Order Requirements

- **Post-only**: OBLIGATORIO (0% fees + 20% rebates)
- **WebSocket**: OBLIGATORIO (NO REST polling)
- **Rate limit**: 3,500/10s burst, 60/s sustained
- **Slippage**: <0.5% target
- **Fill rate**: >95% target

---

## 🎯 Roadmap

### Fase 1: ✅ Estructura (COMPLETADO)
52 dirs, 168 files, Git initialized

### Fase 2: ✅ Config Files (COMPLETADO)
- requirements.txt: 30+ production dependencies (FastAPI, asyncpg, web3, redis)
- requirements-dev.txt: Testing/linting tools (pytest, black, ruff, mypy)
- pyproject.toml: Strict type checking + code quality configs
- pytest.ini: 80% coverage threshold + async support
- .pre-commit-config.yaml: 6 hooks (black, ruff, mypy, gitleaks)
- docker-compose.yml: 16 services (TimescaleDB, Redis, API, Dashboard, Bots, Monitoring)
- docker-compose.dev.yml: Development environment
- docker-compose.test.yml: Test environment
- Makefile: 25 commands (install, test, lint, docker, migrate, backup)

### Fase 3: ✅ Core Services (COMPLETADO)
models.py, redis_client.py, timescaledb.py, event_bus.py, wallet_manager.py, gas_manager.py, websocket_gateway.py, market_data_processor.py, risk_manager.py, order_execution_engine.py

### Fase 4: ✅ Bot 8 Prototype (COMPLETADO)
base_bot.py, tail_risk strategies, market_making strategies, bot_08_tail_risk_combo.py, tests ≥85%, config YAML

### Fase 5: ✅ Dashboard MVP (COMPLETADO)
**Descripción**: Streamlit dashboard multi-page real-time monitoring  
**ETA**: 28h → COMPLETADO

**7 Páginas implementadas**:
1. 🏠 Overview: Emergency controls, metrics cards (1s updates), P&L chart, portfolio composition, zone heatmap
2. 🤖 Bot Control: Bot status grid, detail panel (metrics, charts, config editor, logs, actions), state diagram
3. 📈 Performance: Comparative table, ROI chart, risk-adjusted scatter, drawdown analysis, trade distributions
4. 💰 Positions: Active table (1s updates), position modal, closed history, position heatmap
5. 📜 Order Log: Execution table (2s updates), filters, performance metrics, latency distribution, rejection analysis
6. ⚠️ Risk Monitor: Zone exposure, circuit breaker status, drawdown gauges, consecutive loss tracker, risk alerts feed
7. ⚙️ Settings: 5 tabs (Global config, Bot-specific, Notifications, Database, System health)

**Components Library**:
- metric_card.py: Reusable metric display cards
- chart_utils.py: Common Plotly configurations
- websocket_client.py: Real-time WebSocket connection
- api_client.py: Backend API HTTP client
- state_manager.py: Session state management

**Features Production-Ready**:
- Real-time WebSocket updates (1s-2s)
- Interactive Plotly charts
- Comprehensive bot/position/order/risk monitoring
- Configuration management with validation
- Confirmation dialogs destructive actions
- Loading states async operations
- Error handling graceful
- Type hints mypy strict
- Docstrings Google style
- Responsive layouts

### Fase 6: ✅ Paper Trading (COMPLETADO)
**Descripción**: Paper trading engine para validación risk-free Bot 8  
**Componentes implementados**:

**1. Paper Trading Engine** (`src/application/paper_trading/paper_trading_engine.py`):
- PaperTradingConfig: initial_balance $5K, slippage/fees/latency simulation configurable
- VirtualBalance: available/reserved tracking, total calculation
- VirtualPosition: unrealized P&L, value, side-dependent calculations
- PaperTradingEngine: Complete virtual trading environment
  - place_order: Balance validation, capital reservation, order simulation
  - cancel_order: Instant cancellation, capital release
  - close_position: P&L calculation with fees/slippage, realized tracking
  - Order simulation: POST_ONLY 70% fill probability, latency/slippage/fees realistic
  - Performance tracking: ROI, win rate, Sharpe estimation
  - State reset capability

**2. Paper Trading Use Cases**:
- `RunPaperTradingUseCase`: Orchestrates complete session (duration, strategy execution, performance summary)
- `GetPaperTradingStatsUseCase`: Real-time metrics (balance, positions, P&L, ROI)
- `ResetPaperTradingUseCase`: Clean state reset with audit trail

**3. Features**:
- Realistic simulation: slippage 0.1% avg/0.5% max, fees 2% taker/0% maker, latency 50ms default
- Side-dependent slippage: pay more YES, receive less NO
- Partial fills: realistic fragmentation modeling
- Performance metrics: initial_balance, current_balance, portfolio_value, realized_pnl, unrealized_pnl, total_pnl, total_fees, open_positions, roi
- Safety: No real wallet interaction, no blockchain transactions

**4. Testing**:
- Unit tests: ≥85% coverage
- Integration tests: Complete workflow validation
- Performance tests: Latency benchmarks

**ETA**: 20h → COMPLETADO

### Fase 7: ⏳ Bot 8 Production (EN PROGRESO)
**Descripción**: Bot 8 production deployment con validación paper trading  
**Tareas**:
1. Paper trading validation: 7 days simulation, min 5% ROI, max 15% drawdown
2. Hot wallet setup: BIP39 mnemonic generation, AES-256 encryption, $5K initial funding
3. Production config: YAML tuning based on paper trading results
4. Monitoring setup: Grafana dashboards, alerting rules
5. Gradual rollout: $1K → $2.5K → $5K capital allocation
6. Performance tracking: Daily P&L, Sharpe ratio, max drawdown
7. Circuit breaker validation: Test all 4 circuit breakers
8. Emergency procedures: Document halt/resume workflows

**Acceptance Criteria**:
- Paper trading: ≥5% ROI, ≤15% max drawdown, ≥60% win rate (7 days)
- Production: ≥3% weekly ROI first 2 weeks
- Monitoring: <5min alert latency, 99.9% uptime
- Safety: All circuit breakers functional, emergency halt <10s

**ETA**: 30h → EN PROGRESO

### Fase 8: 🔜 Bots 1-7 Integration (PENDIENTE)
**Descripción**: Integrar y testear Bots 1-7 restantes  
**Por bot (7 bots x 8h = 56h)**:
1. Config YAML: Capital allocation, Kelly fraction, zone restrictions
2. Paper trading: 3 days validation each
3. Unit tests: ≥80% coverage
4. Integration tests: Workflow completo
5. Production deployment: Gradual rollout

**ETA**: 56h

### Fase 9: 🔜 Bots 9-10 Development (PENDIENTE)
**Descripción**: Desarrollar Bots 9-10 desde cero  
**Bot 9 - Kelly Optimizer**:
- Dynamic Kelly fraction adjustment
- Win rate tracking
- Edge recalculation

**Bot 10 - Long-term Value**:
- Macro markets (>90 days)
- Fundamental analysis
- Zone 1-2 mispricing focus

**ETA**: 40h (20h cada bot)

### Fase 10: 🔜 Full Integration Testing (PENDIENTE)
**Descripción**: Testing end-to-end todo el sistema  
**Scope**:
- 10 bots simultáneos
- Load testing: 1000 orders/min
- Failover scenarios: DB down, Redis down, API down
- Circuit breaker stress tests
- Emergency halt workflows
- Wallet rotation procedures

**ETA**: 24h

### Fase 11: 🔜 Production Hardening (PENDIENTE)
**Descripción**: Security audit + performance optimization  
**Tasks**:
- Security audit: gitleaks, bandit, safety
- Performance profiling: cProfile, memory_profiler
- Database tuning: Query optimization, index review
- Rate limit fine-tuning
- Error handling comprehensive review
- Logging audit: Remove sensitive data
- Documentation: Runbooks, incident response

**ETA**: 20h

### Fase 12: ✅ Dashboard Enhancements (COMPLETADO)
**Descripción**: Dashboard completo con 7 páginas interactivas  
**Implementación**:

**Base Structure + Components** (5 commits):
1. app.py: Main Streamlit app, page config, multi-page architecture
2. Components library:
   - metric_card.py: Reusable metric display cards
   - chart_utils.py: Common Plotly configurations
   - websocket_client.py: Real-time WebSocket connection
   - api_client.py: Backend API HTTP client
   - state_manager.py: Session state management

**7 Pages Production-Ready**:

1. **Overview Page** (pages/1_Overview.py):
   - Emergency controls: HALT ALL, PAUSE ALL, RESUME ALL (prominent)
   - Metrics cards: Portfolio Value, Total P&L, Open Positions, Active Bots (1s updates)
   - Charts: P&L cumulative, portfolio composition pie, zone heatmap
   - Bot status grid: Quick view 10 bots

2. **Bot Control Page** (pages/2_Bot_Control.py):
   - Status grid: 10 bots state indicators
   - Detail panel: Metrics (2s), charts (ROI, positions), config YAML editor, logs (last 50), actions (START/STOP/PAUSE/RESUME/HALT)
   - State diagram: Visual lifecycle

3. **Performance Page** (pages/3_Performance.py):
   - Comparative table: All bots (Bot ID, Strategy, ROI, P&L, Win Rate, Sharpe, Positions, Status)
   - Charts: ROI multi-line, risk-adjusted scatter (Sharpe vs ROI), drawdown analysis, P&L histogram, hold times box plot
   - Filtering: Strategy, status, date range
   - Export: CSV download

4. **Positions Page** (pages/4_Positions.py):
   - Active table: 1s updates (Bot, Market, Side, Size, Entry, Current, P&L, Duration, Zone, Status)
   - Position modal: Entry/exit info, P&L breakdown, market context, CLOSE button
   - Closed history: Last 100 (filterable bot_id, date, profit/loss)
   - Charts: Position heatmap (size vs P&L), portfolio value time series
   - Export: CSV active/closed

5. **Order Log Page** (pages/5_Order_Log.py):
   - Execution table: 2s updates (Time, Bot, Market, Side, Type, Size, Price, Status, Fill%, Latency)
   - Order modal: Timeline (submitted → ack → filled), fill breakdown, rejection reason, gas+slippage
   - Filters: Bot, status, time range, order type
   - Metrics cards: Fill rate, avg latency, rejection rate, 24h volume
   - Charts: Latency histogram (p99 100ms target), rejection analysis (pie+bar), size distribution
   - Export: CSV order log

6. **Risk Monitor Page** (pages/6_Risk_Monitor.py):
   - Zone exposure grid: 5 zones, current %, limits, progress bars (GREEN/YELLOW/RED)
   - Circuit breakers: 4 breakers status (ARMED/TRIGGERED), thresholds, auto-reset timers
   - Drawdown gauges: Portfolio (40% threshold), bot-specific (25% threshold), color-coded Plotly
   - Consecutive loss tracker: Per-bot count, 3-loss threshold, recent timeline
   - Risk alerts feed: Last 50 WebSocket alerts, filterable severity (INFO/WARNING/CRITICAL)
   - Zone heatmap: Exposure concentration (drill-down by bot)

7. **Settings Page** (pages/7_Settings.py):
   - **Tab 1 - Global Config**: Emergency controls, risk params (40% portfolio, 5% daily), trading params (POST_ONLY, 0.5% slippage, rate limits), save+validation
   - **Tab 2 - Bot-Specific**: Bot selector, config editor (capital, Kelly, position size, zones, strategy YAML), enable/disable, reset defaults
   - **Tab 3 - Notifications**: Alert channels (email SMTP, webhooks Slack/Discord, SMS Twilio), thresholds (circuit breaker, balance, performance), test button
   - **Tab 4 - Database**: Connection status (TimescaleDB+Redis), metrics (latency p50/p99, pool usage, cache hit rate), maintenance (compression, retention, backup), actions (compress now, clear cache, export snapshot)
   - **Tab 5 - System Health**: Service status grid (API, Dashboard, DB, Redis, WebSocket, 10 bots), resource usage (CPU%, Memory MB, Network I/O), logs viewer (last 100, filter service/level, live tail), system actions (restart, clear logs, diagnostics)

**Integration**:
- FastAPI: 17 routes (/api/v1/bots, /positions, /orders, /metrics, /risk, /config, /health, /wallet)
- WebSocket: Real-time updates (/ws/bots/status, /ws/positions/{bot_id}, /ws/risk/alerts)
- Authentication: X-API-Key header

**Production Features**:
- Input validation: Pydantic all forms
- Confirmation dialogs: Destructive actions (HALT, CLOSE, DELETE)
- Loading spinners: Async operations
- Error handling: User-friendly messages, graceful degradation
- Auto-reconnect: WebSocket on disconnect
- Session persistence: State across navigation
- Type hints: mypy strict
- Docstrings: Google style comprehensive
- Responsive: Mobile/tablet/desktop
- Color-coded: Status indicators (green/yellow/red), performance tiers (Elite/Good/Average/Poor)
- Audit trail: Config changes
- Rollback: Config changes capability

**ETA**: 28h → COMPLETADO (4 commits, 7 páginas, 5 componentes)

### Fase 13: 🔜 Integration Tests (EN PROGRESO)
**Descripción**: Integration tests end-to-end flujos críticos  
**Scope**:

**1. Bot Lifecycle Tests** (`tests/integration/test_bot_lifecycle.py`):
- Test startup: IDLE → STARTING → ACTIVE (estado transitions, DB updates, event publishing)
- Test pause/resume: ACTIVE ⇄ PAUSED (state persistence, position preservation)
- Test stop graceful: ACTIVE → STOPPING → STOPPED (close open positions, cleanup resources)
- Test emergency halt: ANY_STATE → EMERGENCY_HALT (immediate stop, alert publishing, audit trail)
- Test error recovery: ERROR → retry → ACTIVE or STOPPED
- Fixtures: Test bots, mock external services, DB cleanup

**2. Order Flow Tests** (`tests/integration/test_order_flow.py`):
- Test order placement: Risk validation → order creation → DB save → event publish → CLOB submission
- Test order fill: WebSocket update → position creation → P&L calculation → metrics update
- Test partial fill: Multiple fill events → position accumulation → average entry price
- Test order rejection: CLOB rejection → status update → capital release → retry logic
- Test order cancel: Cancel request → CLOB cancel → capital release → DB update
- Test POST_ONLY enforcement: Order type validation, fee calculation, maker rebate
- Test slippage limits: Slippage calculation, max threshold enforcement
- Fixtures: Mock CLOB client, test markets, virtual balances

**3. Risk Management Tests** (`tests/integration/test_risk_management.py`):
- Test zone restrictions: Validate zone classification, enforce directional ban Z4-Z5, allow arb/MM all zones
- Test circuit breaker consecutive losses: 3 losses → pause 24h → auto-resume
- Test circuit breaker daily loss: 5% daily → halt all → manual resume required
- Test circuit breaker bot drawdown: 25% → halt bot → manual resume
- Test circuit breaker portfolio drawdown: 40% → emergency halt → manual resume
- Test Kelly sizing: Half/Quarter/Full Kelly calculation, edge validation, max position size
- Test exposure limits: Max 40% per outcome (Bot 6), max 30% inventory skew (Bot 5)
- Test risk metrics calculation: Current drawdown, consecutive losses, open exposure
- Fixtures: Mock risk events, test positions, circuit breaker state

**4. Wallet Integration Tests** (`tests/integration/test_wallet_integration.py`):
- Test balance tracking: Real-time balance updates, USDC/MATIC tracking, pending tx consideration
- Test nonce management: Redis lock acquisition, nonce increment, blockchain sync, collision prevention
- Test gas estimation: Gas limit calculation, EIP-1559 pricing, adaptive strategy (rapid/fast/standard/queue)
- Test transaction signing: Local signing (eth_account), signature validation, NEVER send private key
- Test transaction submission: RPC submission, pending tracking, confirmation polling, stuck detection
- Test auto-rebalance: Trigger <5% threshold, transfer cold→hot, update balances, alert publishing
- Test emergency withdrawal: Transfer ALL to cold, halt all bots, audit trail
- Fixtures: Mock blockchain RPC, test wallets (hot/cold), Redis nonce state

**5. Database Performance Tests** (`tests/integration/test_database_performance.py`):
- Test query latency: Simple queries <10ms p99, aggregations <50ms p99, dashboard <100ms p99
- Test write throughput: 1000 orders/min sustained, 10ms p99 write latency
- Test hypertable chunks: 7-day chunks orders/positions/trades, 1-day chunks market_snapshots
- Test compression: 14d policy orders/positions/trades, 7d policy market_snapshots, 4-5x ratio validation
- Test continuous aggregates: bot_performance_hourly, bot_pnl_daily, market_price_5min refresh
- Test retention: 365d orders/positions/trades, 90d market_snapshots, auto-cleanup
- Test connection pooling: Max connections, idle timeout, connection reuse
- Fixtures: Test hypertables, sample data generation, cleanup policies

**6. WebSocket Integration Tests** (`tests/integration/test_websocket_integration.py`):
- Test orderbook subscription: Subscribe market_id, receive updates <100ms, price/liquidity tracking
- Test trade feed subscription: Subscribe bot_id, receive trade executions, update positions
- Test event stream subscription: Subscribe event_type, receive domain events (OrderPlaced, PositionClosed, CircuitBreakerTriggered)
- Test auto-reconnect: Simulate disconnect, reconnect exponential backoff (1s, 2s, 4s, 8s max), resubscribe all channels
- Test heartbeat: Send ping every 30s, expect pong <5s, disconnect if timeout
- Test message ordering: Validate sequence numbers, detect gaps, request replay if missing
- Test rate limiting: Dashboard 1s updates, API 100 req/min, CLOB 3500/10s burst
- Fixtures: Mock WebSocket server, test channels, message sequences

**7. Dashboard API Tests** (`tests/integration/test_dashboard_api.py`):
- Test metrics endpoint: /api/v1/metrics/portfolio, /api/v1/metrics/bots/{id}, real-time data
- Test bot control endpoints: POST /api/v1/bots/{id}/start, /stop, /pause, /resume, state transitions
- Test position endpoints: GET /api/v1/positions, POST /api/v1/positions/{id}/close, P&L calculation
- Test order endpoints: GET /api/v1/orders, POST /api/v1/orders/place, DELETE /api/v1/orders/{id}
- Test risk endpoints: GET /api/v1/risk/metrics, GET /api/v1/risk/circuit-breakers, POST /api/v1/risk/emergency-halt
- Test config endpoints: GET /api/v1/config/global, PUT /api/v1/config/global, GET /api/v1/config/bots/{id}, PUT /api/v1/config/bots/{id}
- Test health endpoints: GET /health/live, GET /health/ready, GET /health/startup
- Test authentication: X-API-Key header validation, 401 unauthorized
- Test rate limiting: 100 req/min per client, 429 too many requests
- Fixtures: Test API client, mock backend services, auth tokens

**8. Paper Trading Integration Tests** (`tests/integration/test_paper_trading_integration.py`):
- Test complete session: Initialize $5K → place orders → simulate fills → close positions → calculate performance
- Test order simulation: POST_ONLY 70% fill, MARKET instant, slippage 0.1% avg/0.5% max, latency 50ms
- Test position tracking: Open position → unrealized P&L calculation → close position → realized P&L
- Test performance metrics: ROI calculation, win rate tracking, Sharpe ratio estimation
- Test state reset: Clean reset → initial balance restored → positions cleared → stats reset
- Test Bot 8 validation: 7 days simulation, ≥5% ROI target, ≤15% max drawdown, ≥60% win rate
- Fixtures: Paper trading engine, test strategies, mock market data

**Test Infrastructure**:
- Testcontainers: TimescaleDB, Redis containers (isolated test DBs)
- Fixtures: Shared fixtures module (test_fixtures.py)
- Async support: pytest-asyncio for async tests
- Coverage: ≥80% threshold (pytest-cov)
- CI/CD: GitHub Actions run on every push
- Performance benchmarks: Track latency trends, alert regressions

**Acceptance Criteria**:
- All 8 integration test suites pass
- Coverage ≥80% integration code
- Latency budgets met: <10ms simple, <50ms aggregation, <100ms dashboard
- No flaky tests: 100 consecutive runs pass
- CI/CD green: All tests pass on main branch

**ETA**: 32h (8 suites x 4h)

---

## 📊 Estado Actual

**Fase actual**: Fase 13 (Integration Tests)  
**Progreso global**: ~75% (Fases 1-6 + Fase 12 completadas, Fase 7 en progreso, Fases 8-13 pendientes)  
**Último commit**: 2026-02-13 01:58:53 UTC  
**Branch**: main  
**Estado**: Clean working directory  

**Completado**:
- ✅ Fase 1: Estructura (168 files)
- ✅ Fase 2: Config files (Docker, requirements, pre-commit)
- ✅ Fase 3: Core services (10 services production-ready)
- ✅ Fase 4: Bot 8 Prototype (tests ≥85%)
- ✅ Fase 5: Dashboard MVP (7 páginas interactivas)
- ✅ Fase 6: Paper Trading (engine + use cases + tests)
- ✅ Fase 12: Dashboard Enhancements (7 páginas production-ready, 5 componentes, WebSocket real-time, Plotly charts, comprehensive monitoring)

**En progreso**:
- ⏳ Fase 7: Bot 8 Production (paper trading validation)
- ⏳ Fase 13: Integration Tests (8 suites x 4h = 32h)

**Próximos pasos**:
1. Implementar Fase 13: Integration Tests (8 test suites)
2. Continuar Fase 7: Bot 8 Production deployment
3. Fase 8: Bots 1-7 Integration (7 bots)
4. Fase 9: Bots 9-10 Development (2 bots nuevos)
5. Fase 10: Full Integration Testing (load, failover)
6. Fase 11: Production Hardening (security, performance)

---

## 🚫 Reglas CRÍTICAS (NUNCA violar)

### Arquitectura
1. ❌ Cambiar arquitectura sin ADR aprobado
2. ❌ Violar dependency rule (outer → inner)
3. ❌ Business logic en infrastructure/presentation
4. ❌ Infrastructure concerns en domain

### Trading
5. ❌ REST polling (WebSocket OBLIGATORIO)
6. ❌ Taker orders (Post-only OBLIGATORIO)
7. ❌ Full Kelly (Half/Quarter SOLO)
8. ❌ Directional betting Z4-Z5 (Arb/MM solo)
9. ❌ Skip risk validation
10. ❌ Exceed circuit breaker thresholds

### Código
11. ❌ Código sin type hints
12. ❌ Funciones públicas sin docstrings
13. ❌ `except:` bare (specify exception)
14. ❌ Secrets hardcoded
15. ❌ Log private keys (ni debug)
16. ❌ Blocking I/O en async functions
17. ❌ SQL injection vulnerable (use params)
18. ❌ Full table scans (use indices)

### Testing & Deployment
19. ❌ Merge PR <80% coverage
20. ❌ Commit WIP/fix/temp messages
21. ❌ Push broken code
22. ❌ Deploy sin paper trading validation
23. ❌ Skip pre-commit hooks
24. ❌ Ignore linter errors

---

## ✅ Criterios de Aceptación (TODAS las tareas)

### Código
- ✅ Type hints completos (mypy --strict clean)
- ✅ Docstrings públicas (Google style)
- ✅ Tests ≥80% coverage
- ✅ black, ruff, mypy clean
- ✅ Error handling robusto (Result[T,E] pattern)
- ✅ Logging JSON structured

### Git
- ✅ Conventional commits: `type(scope): subject`
- ✅ Pre-commit hooks pass
- ✅ gitleaks clean (no secrets)
- ✅ Commits atómicos (1 feature/fix)

### Performance
- ✅ Simple queries <10ms p99
- ✅ Aggregations <50ms p99
- ✅ Dashboard <100ms p99
- ✅ Memory leaks: none

### Security
- ✅ Secrets en env vars
- ✅ Private keys encrypted AES-256
- ✅ Input validation (Pydantic)
- ✅ SQL injection protected
- ✅ Rate limiting enforced

### Resilience
- ✅ Circuit breakers functional
- ✅ Auto-reconnect WebSocket
- ✅ Graceful degradation
- ✅ Error recovery tested

---

## 🎯 Objetivo Final

**Sistema operando 24/7**:
- 10 bots activos simultáneos
- $50K capital total ($5K cada bot)
- Target: 8-12% ROI mensual
- Max drawdown: 15% por bot, 40% portfolio
- Uptime: 99.9% (43min downtime/mes max)
- Latency: <100ms p99 dashboard
- Win rate: ≥60% promedio
- Sharpe ratio: ≥1.5 target

**Production-grade desde día 1**: Testing exhaustivo, monitoring completo, circuit breakers robustos, wallet management seguro, paper trading validation ANTES de real money.

---

**Última actualización**: 2026-02-13 02:48 CET  
**Actualizado por**: Contexto automático post Fase 12 completada