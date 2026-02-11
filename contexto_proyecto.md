═══════════════════════════════════════════════════════════════════════════════
POLYMARKET ELITE TRADING SYSTEM (PETS) - CONTEXTO ULTRA-PROFESIONAL V5.0
EXCELENCIA DESDE PRIMERA ITERACIÓN - NO REQUIERE REFINAMIENTO
═══════════════════════════════════════════════════════════════════════════════

🎯 CONTEXTO DEL PROYECTO
Sistema institucional de 10 bots de trading para Polymarket prediction markets operando en el 0.04% elite que captura 70% de profits totales. Stack: Python 3.11+, TimescaleDB, Redis, Docker Compose, Streamlit, FastAPI, Web3.py. Production-grade desde día 1.

📦 REPOSITORIO GITHUB
URL: https://github.com/juankaspain/PETS
Rama: main (commits directos, fast-forward only)
Acceso: MCP GitHub con permisos R/W
Workflow: Feature → Test → Commit → Push → Verify

═══════════════════════════════════════════════════════════════════════════════
⚡ PROTOCOLO OBLIGATORIO AL INICIO DE CADA HILO (FASE 0)
═══════════════════════════════════════════════════════════════════════════════

SIEMPRE ejecutar en este orden exacto:

1. VALIDACIÓN DE ACCESO (15 segundos max)
   ✓ Verificar MCP GitHub conexión activa
   ✓ Confirmar permisos R/W en juankaspain/PETS
   ✓ git log --oneline -5 (últimos 5 commits con hash, autor, timestamp)
   ✓ git status (verificar working tree clean, sin conflictos)
   ✓ git diff --name-only origin/main main (verificar sincronización)
   ✓ Output obligatorio: "✅ Acceso validado | Branch: main | HEAD: [hash] '[mensaje]' por [autor] hace [tiempo] | Status: clean"
   ✗ Si falla: Abortar operación, reportar error detallado con solución propuesta, NO continuar

2. SINCRONIZACIÓN DE ESTADO (20 segundos max)
   ✓ git ls-tree -r main --name-only | wc -l (contar archivos actuales)
   ✓ Comparar contra target: 168 archivos esperados en estructura completa
   ✓ find . -mtime -1 -type f (archivos modificados últimas 24h)
   ✓ Identificar fase actual basado en archivos existentes
   ✓ Output obligatorio: "📊 Progreso: X/168 archivos (Y.Z%) | Fase actual: [N] [nombre] | Última modificación: [archivo] hace [tiempo]"

3. ANÁLISIS DE CONTEXTO (10 segundos max)
   ✓ git log --since="24 hours ago" --name-status (cambios recientes con tipos)
   ✓ Leer archivos relacionados con próxima tarea lógica
   ✓ Verificar imports/dependencies del código existente
   ✓ Identificar tests existentes relacionados
   ✓ Output obligatorio: "🔍 Contexto: [resumen últimos cambios] | Próxima tarea lógica: [archivo/feature] | Dependencies: [lista]"

4. VALIDACIÓN DE ROADMAP (5 segundos max)
   ✓ Confirmar fase actual y prioridad (Bot 8 primero por evidencia $106K)
   ✓ Detectar blockers o dependencies pendientes
   ✓ Estimar ETA para próxima entrega
   ✓ Output obligatorio: "🎯 Prioridad: [tarea] | Blocker: [ninguno/detalles] | ETA: [horas/días] | Razón: [justificación basada en evidencia]"

TIEMPO TOTAL FASE 0: <60 segundos
SI FALLA: Reportar error, proponer solución, esperar confirmación usuario

═══════════════════════════════════════════════════════════════════════════════
🏗️ ARQUITECTURA CLEAN ARCHITECTURE + DDD + HEXAGONAL (ONION ARCHITECTURE)
═══════════════════════════════════════════════════════════════════════════════

DEPENDENCY RULE ESTRICTA: Inner layers NUNCA conocen outer layers
Todas las dependencies apuntan hacia el centro (domain)

CAPA 1: DOMAIN LAYER (src/domain/) - CORE BUSINESS LOGIC
   Entities (src/domain/entities/):
   - Bot: bot_id, strategy_type, state, config, capital_allocated, created_at
   - Order: order_id, bot_id, market_id, side, size, price, zone, status, timestamp
   - Position: position_id, bot_id, order_id, market_id, side, size, entry_price, current_price, pnl, zone, opened_at
   - Market: market_id, question, outcomes, liquidity, volume, created_at, resolves_at
   - Trade: trade_id, order_id, executed_price, executed_size, fees_paid, slippage, timestamp
   - Wallet: address, balance_usdc, balance_matic, nonce, last_sync_at
   
   Value Objects (src/domain/value_objects/):
   - Price(value: Decimal, zone: int) - Immutable, validates 0.01-0.99, auto-classifies zone
   - Quantity(value: Decimal, decimals: int) - Immutable, validates >0
   - OrderId(value: str) - NewType, validates UUID format
   - MarketId(value: str) - NewType, validates hex format
   - Side(Enum) - YES, NO
   - OrderStatus(Enum) - PENDING, FILLED, PARTIALLY_FILLED, CANCELED, REJECTED, EXPIRED
   - BotState(Enum) - IDLE, STARTING, ACTIVE, PAUSED, STOPPING, STOPPED, ERROR, EMERGENCY_HALT
   - Zone(Enum) - ZONE_1, ZONE_2, ZONE_3, ZONE_4, ZONE_5 (con ranges y restrictions)
   
   Domain Services (src/domain/services/):
   - RiskCalculator: calculate_position_risk, validate_order_risk, check_drawdown
   - KellyCalculator: calculate_kelly_fraction (Half/Quarter), validate_edge
   - ZoneClassifier: classify_price_zone, validate_zone_restrictions
   - PnLCalculator: calculate_realized_pnl, calculate_unrealized_pnl, calculate_sharpe_ratio
   - FeeCalculator: calculate_taker_fee (dynamic 0-3.15%), calculate_maker_rebate (20%)
   - GasEstimator: estimate_gas_limit, calculate_gas_cost_usdc, optimize_gas_price
   
   Domain Events (src/domain/events/):
   - OrderPlacedEvent(order_id, bot_id, market_id, timestamp)
   - PositionOpenedEvent(position_id, bot_id, size, entry_price, zone)
   - PositionClosedEvent(position_id, realized_pnl, hold_duration)
   - CircuitBreakerTriggeredEvent(bot_id, reason, threshold_value, current_value)
   - EmergencyHaltEvent(trigger_reason, affected_bots, timestamp)
   - DrawdownThresholdEvent(bot_id, current_drawdown, threshold)
   - WalletBalanceLowEvent(wallet_address, balance_usdc, threshold)
   - GasSpikeyDetectedEvent(current_gwei, threshold_gwei, action)
   
   Repository Interfaces/Protocols (src/domain/repositories/):
   - BotRepository(Protocol): save, find_by_id, find_active, update_state
   - OrderRepository(Protocol): save, find_by_id, find_by_bot_id, update_status
   - PositionRepository(Protocol): save, find_open_by_bot, close_position
   - MarketRepository(Protocol): find_by_id, find_active, update_liquidity
   - WalletRepository(Protocol): get_balance, update_balance, get_nonce
   
   Domain Exceptions (src/domain/exceptions/):
   PETSError (base)
   ├── DomainError
   │   ├── OrderError
   │   │   ├── InvalidOrderError(order_id, reason)
   │   │   ├── InsufficientBalanceError(required, available)
   │   │   ├── OrderRejectedError(order_id, polymarket_reason)
   │   │   └── DuplicateOrderError(order_id)
   │   ├── PositionError
   │   │   ├── PositionNotFoundError(position_id)
   │   │   └── PositionAlreadyClosedError(position_id)
   │   ├── RiskViolation
   │   │   ├── ZoneViolationError(zone, restriction_type)
   │   │   ├── DrawdownExceededError(current, threshold, bot_id)
   │   │   ├── ExposureLimitError(current_exposure, limit, category)
   │   │   └── ConsecutiveLossesError(count, threshold)
   │   ├── WalletError
   │   │   ├── InsufficientGasError(required_matic, available_matic)
   │   │   ├── InsufficientUSDCError(required_usdc, available_usdc)
   │   │   ├── NonceOutOfSyncError(expected, actual)
   │   │   └── WalletLockedError(reason)
   │   └── CircuitBreakerOpenError(service, state, time_remaining)

CAPA 2: APPLICATION LAYER (src/application/) - USE CASES + ORCHESTRATION
   Use Cases (src/application/use_cases/):
   - PlaceOrderUseCase(order_dto, risk_manager, order_executor, event_bus) -> Result[OrderId, OrderError]
   - OpenPositionUseCase(position_dto, wallet_manager, position_repo) -> Result[PositionId, PositionError]
   - ClosePositionUseCase(position_id, current_price, position_repo) -> Result[PnL, PositionError]
   - CalculateRiskUseCase(order_dto, current_positions, risk_calculator) -> Result[None, RiskViolation]
   - ExecuteBotStrategyUseCase(bot_id, market_data, strategy, risk_manager) -> Result[List[Order], BotError]
   - EmergencyHaltUseCase(reason, bot_manager, position_closer, event_bus) -> Result[HaltReport, HaltError]
   - TopUpWalletUseCase(wallet_address, amount_usdc, wallet_manager) -> Result[TxHash, WalletError]
   - RebalanceWalletUseCase(min_balance_usdc, wallet_manager, treasury) -> Result[TxHash, WalletError]
   - ValidateZoneRestrictionUseCase(price, strategy_type, zone_classifier) -> Result[None, ZoneViolation]
   - CalculateKellySizeUseCase(probability, odds, capital, kelly_calculator) -> Result[Decimal, ValueError]
   
   DTOs (Data Transfer Objects) (src/application/dtos/):
   - OrderDTO(market_id, side, size, price, bot_id, strategy_type, post_only, time_in_force)
   - PositionDTO(bot_id, market_id, side, size, entry_price, stop_loss, take_profit)
   - MarketDataDTO(market_id, yes_price, no_price, liquidity, volume_24h, last_update)
   - RiskMetricsDTO(bot_id, current_drawdown, consecutive_losses, open_exposure, zone_distribution)
   - WalletBalanceDTO(address, usdc_balance, matic_balance, pending_transactions, last_sync)
   
   Application Services (src/application/services/):
   - TransactionCoordinator: Coordina múltiples use cases en transacción (order + position + wallet)
   - EventPublisher: Publica domain events al event bus
   - CacheInvalidator: Invalida caches cuando domain events ocurren
   
   REGLA: Application layer es stateless, no contiene business logic (eso está en domain)

CAPA 3: INFRASTRUCTURE LAYER (src/infrastructure/) - EXTERNAL INTEGRATIONS
   Repositories (src/infrastructure/repositories/):
   - TimescaleDBOrderRepository(implements OrderRepository)
   - TimescaleDBPositionRepository(implements PositionRepository)
   - RedisPositionRepository(implements PositionRepository) - Hot data cache
   - TimescaleDBMarketRepository(implements MarketRepository)
   - RedisWalletRepository(implements WalletRepository)
   
   External Services (src/infrastructure/external/):
   - PolymarketCLOBClient: HTTP client con HMAC-SHA256 auth, rate limiting, retry logic
   - PolymarketWebSocketClient: Persistent WebSocket con auto-reconnect, heartbeat
   - PolygonRPCClient: Web3.py wrapper, connection pooling, nonce management
   - NewsAPIClient: Multi-source aggregator (NewsAPI, Bloomberg, Reuters RSS)
   - EsportsAPIClient: Riot Games, Steam, Abios, PandaScore integrations
   - KaitoAPIClient: Attention markets + social sentiment
   
   Persistence (src/infrastructure/persistence/):
   - SQLAlchemy models (ORM mapping):
     * BotModel, OrderModel, PositionModel, TradeModel, MarketModel, WalletModel
     * Migrations con Alembic (timestamped, reversible)
   - Redis schemas (JSON serialization):
     * OrderBookSchema, PositionSnapshotSchema, WalletStateSchema
   - TimescaleDB hypertables (automatic partitioning):
     * orders (partitioned by timestamp, 7-day chunks)
     * positions (partitioned by timestamp, 7-day chunks)
     * trades (partitioned by timestamp, 7-day chunks)
     * market_snapshots (partitioned by timestamp, 1-day chunks)
   
   Messaging (src/infrastructure/messaging/):
   - RedisPubSubEventBus(implements EventBus):
     * Channels: orderbook.{market_id}, trades.{bot_id}, events.{event_type}
     * Serialization: JSON + gzip (if payload >1KB)
     * Delivery guarantee: At-least-once
     * Consumer groups: Multiple consumers per channel
   
   Wallet Management (src/infrastructure/wallet/):
   - WalletManager:
     * Hot wallet: Para trading (mantiene balance 10-20% total capital)
     * Cold wallet: Storage mayoritario (80-90% capital)
     * Auto-rebalance: Si hot wallet <5% capital, transfer desde cold
     * Gas optimization: Batch transactions cuando posible
     * Nonce tracking: Redis-based con locks distribuidos
     * Transaction signing: Local con eth_account, nunca enviar private key
     * Recovery: BIP39 mnemonic phrase backup (encrypted en cold storage)
   
   - GasManager:
     * Monitor gas prices: Polygon Gas Station API (refresh 10s)
     * Adaptive gas price: Use 'fast' tier si <30 gwei, 'standard' si <50 gwei
     * Gas spike protection: Queue transactions si >100 gwei, alert usuario
     * Gas cost tracking: Log gas spent por bot para ROI calculation
     * Gas optimization techniques:
       - EIP-1559: Use maxPriorityFeePerGas = 30 gwei, maxFeePerGas = base + 30
       - Nonce batching: Submit múltiples txs con nonces consecutivos
       - Gas limit tuning: Use 21000 para transfers, 150000 para contract calls
   
   - WalletRecovery:
     * Mnemonic backup: 24-word phrase encrypted con AES-256, stored offline
     * Multi-sig support (futuro): 2-of-3 multisig para cold wallet
     * Emergency withdrawal: Function para extraer fondos si bot compromised
     * Wallet rotation: Support cambiar wallets sin downtime (dual-wallet mode)

CAPA 4: PRESENTATION LAYER (src/presentation/) - USER INTERFACES
   API (src/presentation/api/):
   - FastAPI application con versioning: /api/v1/
   - Routes (17 total):
     * /bots: GET (list), GET /{id} (detail), POST /{id}/start, POST /{id}/stop, POST /{id}/pause, PUT /{id}/config
     * /positions: GET (list), GET /{id} (detail), POST /{id}/close
     * /orders: GET (list), GET /{id} (detail), POST (place), DELETE /{id} (cancel)
     * /metrics: GET /bots/{id}, GET /portfolio, GET /prometheus (Prometheus format)
     * /health: GET /live (liveness), GET /ready (readiness), GET /startup
     * /wallet: GET /balance, POST /topup, POST /rebalance, GET /transactions
     * /risk: GET /metrics, GET /circuit-breakers, POST /emergency-halt
   - Middleware:
     * AuthMiddleware: API key validation (X-API-Key header)
     * RateLimitMiddleware: 100 req/min per client (Redis-backed)
     * CORSMiddleware: Allow dashboard origin
     * RequestIDMiddleware: Generate correlation_id for tracing
     * LoggingMiddleware: Log all requests/responses (structured JSON)
     * ErrorHandlerMiddleware: Catch exceptions, return consistent error format
   
   Dashboard (src/presentation/dashboard/):
   - Streamlit multi-page app con real-time WebSocket updates
   
   PÁGINAS (7 total):
   
   1. 🏠 Overview (src/dashboard/pages/1_🏠_Overview.py):
      Layout: 3 columnas con métricas, luego full-width charts
      
      Top Section - Emergency Controls:
      [🔴 EMERGENCY HALT ALL] [🟢 START ALL BOTS] [🟡 PAUSE ALL BOTS] [🔵 RELOAD CONFIGS]
      
      Metrics Cards (1s updates via WebSocket):
      ┌────────────────┬────────────────┬────────────────┬────────────────┐
      │ Total P&L      │ Portfolio ROI  │ Sharpe Ratio   │ Max Drawdown   │
      │ $6,234.50 ⬆️   │ +12.47% 📈     │ 1.52 🟢        │ -8.3% 🟢       │
      │ Today: +$187   │ Target: >10%   │ Target: >1.2   │ Limit: 40%     │
      └────────────────┴────────────────┴────────────────┴────────────────┘
      ┌────────────────┬────────────────┬────────────────┬────────────────┐
      │ Win Rate       │ Total Trades   │ Avg Latency    │ Active Bots    │
      │ 58.3% 🟢       │ 1,247          │ 87ms 🟢        │ 8/10           │
      │ Target: >55%   │ Today: 47      │ Budget: 200ms  │                │
      └────────────────┴────────────────┴────────────────┴────────────────┘
      
      Real-time P&L Chart (5s updates, Plotly):
      - Dual-axis chart: Lines (P&L por bot 10 colores) + Bar (volume diario)
      - Time range selector: 1H, 6H, 24H, 7D, 30D, ALL
      - Hover tooltip: Timestamp, bot name, P&L, cumulative P&L, trade details
      - Zoom/pan enabled, crosshair cursor
      - Annotations para eventos: Circuit breaker, emergency halt, config change
      
      Portfolio Composition (Donut chart):
      - Capital allocation por bot con % y $ amount
      - Color-coded por tipo: Agresivo (rojo), Neutro-Agresivo (amarillo), Poco Agresivo (verde)
      - Click para filtrar datos por bot
      
      Zone Distribution Heatmap:
      - 5x10 grid: Rows = Zones 1-5, Columns = Bots 1-10
      - Cell color intensity = % capital en esa zona
      - Red alert si >10% capital en Zone 4-5 para bets direccionales
      - Tooltip: Bot ID, zone, % capital, # positions, avg hold time
   
   2. 🤖 Bot Control (src/dashboard/pages/2_🤖_Bot_Control.py):
      Layout: 2 columnas, bot list izquierda, detalles derecha
      
      Bot Status Grid (left column):
      ┌─────────────────────────────────────────────────────┐
      │ Bot 1: Market Rebalancing  [🟢 ACTIVE] [⏸️][⏹️][⚙️] │
      │ ROI: +8.2% | Trades: 142 | Win: 73.2% | P&L: +$410 │
      ├─────────────────────────────────────────────────────┤
      │ Bot 8: Tail Risk + MM      [🟢 ACTIVE] [⏸️][⏹️][⚙️] │
      │ ROI: +32.1% | Trades: 89 | Win: 56.2% | P&L: +$2.1K│
      ├─────────────────────────────────────────────────────┤
      │ Bot 3: Copy Trading        [🟡 PAUSED] [▶️][⏹️][⚙️] │
      │ ROI: +5.1% | Trades: 23 | Win: 52.2% | P&L: +$128 │
      └─────────────────────────────────────────────────────┘
      
      Bot Detail Panel (right column, select bot from grid):
      - Real-time metrics: Current positions, open orders, recent trades
      - Performance charts: ROI trend, drawdown curve, win rate evolution
      - Configuration editor: YAML config con syntax highlighting, save button
      - Logs viewer: Last 100 log entries, filter by level, search
      - Action buttons: Start, Pause, Stop, Restart, Emergency Stop
      
      Bot Lifecycle State Diagram:
      IDLE → STARTING → ACTIVE ⇄ PAUSED
                ↓         ↓        ↓
              ERROR ← STOPPING ← EMERGENCY_HALT
                ↓
              STOPPED
   
   3. 📈 Performance (src/dashboard/pages/3_📈_Performance.py):
      
      Comparative Performance Table:
      | Bot | Strategy | ROI % | Sharpe | Drawdown | Win Rate | Trades | Best Trade | Worst Trade | Avg Hold |
      |-----|----------|-------|--------|----------|----------|--------|------------|-------------|----------|
      | 8   | Tail+MM  | 32.1% | 1.82   | -6.2%    | 56.2%    | 89     | +$412      | -$87        | 4h 23m   |
      | 2   | Esports  | 28.3% | 1.65   | -9.1%    | 62.1%    | 34     | +$523      | -$134       | 1h 45m   |
      | 5   | MM       | 14.2% | 1.43   | -4.8%    | 68.3%    | 287    | +$89       | -$42        | 8h 12m   |
      
      ROI Comparison Chart (Plotly line chart):
      - Y-axis: ROI %, X-axis: Time
      - 10 lines (bots) con legend, toggle visibility
      - Shaded area: Target ROI zone (10-15%)
      
      Risk-Adjusted Returns Scatter Plot:
      - X-axis: Volatility (stddev of returns)
      - Y-axis: Sharpe Ratio
      - Bubbles: Bots (size = capital allocated)
      - Quadrants: Low risk/Low return, High risk/Low return, Low risk/High return, High risk/High return
      - Ideal zone: Top-left (high Sharpe, low vol)
      
      Drawdown Analysis:
      - Underwater chart: % below peak equity
      - Bars: Drawdown duration
      - Annotations: Recovery time per drawdown
      
      Trade Distribution Histograms:
      - P&L histogram: Distribution of trade profits/losses
      - Hold time histogram: Distribution of position durations
      - Size histogram: Distribution of position sizes
   
   4. 💰 Positions (src/dashboard/pages/4_💰_Positions.py):
      
      Active Positions Table (1s updates):
      | Bot | Market | Side | Size | Entry | Current | P&L | P&L% | Zone | Duration | Unrealized |
      |-----|--------|------|------|-------|---------|-----|------|------|----------|------------|
      | 8   | VALORANT Fuego win | YES | 100 | $0.10 | $0.15 | +$5 | +50% | Z1 | 2h 15m | +$5.00 |
      | 5   | BTC >$100K by Mar | YES | 500 | $0.52 | $0.48 | -$20 | -4% | Z3 | 45m | -$20.00 |
      
      Actions: [Close Position] [Adjust Stop Loss] [Adjust Take Profit] [View Details]
      
      Position Details Modal (click row):
      - Entry: Price, timestamp, order ID, transaction hash
      - Current: Price, P&L (realized + unrealized), % change
      - Market info: Question, outcomes, liquidity, volume, resolves at
      - Risk metrics: Zone, max loss, position size % of capital
      - Chart: Price evolution since entry with entry/current markers
      - Actions: Close, adjust stop/take profit, notes field
      
      Closed Positions History (paginated table):
      - Filter: Date range, bot, market category, P&L (profit/loss/all)
      - Sort: By close date, P&L, hold duration, ROI%
      - Export: CSV download with all details
      
      Position Heatmap (by market category):
      - Rows: Categories (Crypto, Politics, Sports, Entertainment, etc.)
      - Columns: Bots
      - Cell intensity: # open positions
      - Tooltip: Total exposure $, avg P&L%, list of markets
   
   5. 📜 Order Log (src/dashboard/pages/5_📜_Order_Log.py):
      
      Order Execution Table (2s updates, last 1000 orders):
      | Timestamp | Bot | Market | Side | Size | Price | Type | Status | Fill Time | Slippage | Fees | Order ID |
      |-----------|-----|--------|------|------|-------|------|--------|-----------|----------|------|----------|
      | 21:45:32  | 8   | VALORANT... | YES | 100 | $0.10 | POST | FILLED | 87ms | -0.2% | $0.00 | abc123... |
      | 21:44:18  | 5   | BTC >... | NO | 250 | $0.48 | POST | FILLED | 124ms | +0.1% | $0.00 | def456... |
      | 21:43:05  | 1   | ETH >... | YES | 150 | $0.35 | POST | REJECTED | N/A | N/A | N/A | ghi789... |
      
      Color coding: 🟢 FILLED, 🟡 PARTIALLY_FILLED, 🔴 REJECTED/CANCELED, ⚪ PENDING
      
      Filters:
      - Time range: Last 1H, 6H, 24H, 7D, Custom
      - Bot: All, Bot 1-10
      - Status: All, Filled, Rejected, Pending
      - Type: All, POST (maker), TAKE (taker)
      
      Order Performance Metrics:
      ┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
      │ Fill Rate       │ Avg Fill Time   │ Avg Slippage    │ Maker Orders    │
      │ 96.2% 🟢        │ 92ms 🟢         │ +0.03% 🟢       │ 98.1% 🟢        │
      │ Target: >95%    │ Budget: 200ms   │ Target: <0.5%   │ Target: >95%    │
      └─────────────────┴─────────────────┴─────────────────┴─────────────────┘
      
      Latency Distribution Chart (histogram):
      - X-axis: Latency buckets (<50ms, 50-100ms, 100-150ms, 150-200ms, >200ms)
      - Y-axis: # orders
      - Color: Green <100ms, Yellow 100-200ms, Red >200ms
      - Overlay: p50, p95, p99 lines
      
      Rejection Analysis:
      - Pie chart: Rejection reasons (Insufficient balance, Price moved, Rate limit, etc.)
      - Table: Top 10 rejected orders with reason and action taken
   
   6. ⚠️ Risk Monitor (src/dashboard/pages/6_⚠️_Risk_Monitor.py):
      
      Risk Dashboard Layout: 4 quadrants
      
      Q1: Zone Exposure (Top-left):
      Stacked bar chart (horizontal):
      - Y-axis: Bots 1-10
      - X-axis: % capital
      - Segments: Zone 1 (green), Zone 2 (blue), Zone 3 (yellow), Zone 4 (orange), Zone 5 (red)
      - Alert line: 10% in Zone 4-5 for directional bets
      - Tooltip: Bot, zone, $ amount, # positions
      
      Q2: Circuit Breaker Status (Top-right):
      Grid of circuit breaker cards:
      ┌──────────────────────────────┐
      │ Bot 8: Tail Risk + MM        │
      │ Status: 🟢 CLOSED (Normal)   │
      │ Consecutive Losses: 0/3      │
      │ Drawdown: 6.2% / 25%         │
      │ Daily Loss: 1.2% / 5%        │
      └──────────────────────────────┘
      ┌──────────────────────────────┐
      │ External: Polymarket API     │
      │ Status: 🟢 CLOSED (Normal)   │
      │ Failures: 0/5                │
      │ Last Success: 2s ago         │
      │ Next Test: 58s               │
      └──────────────────────────────┘
      
      Color coding: 🟢 CLOSED (normal), 🟡 HALF_OPEN (testing), 🔴 OPEN (failing)
      
      Q3: Drawdown Monitor (Bottom-left):
      Real-time drawdown gauges (speedometer style):
      - Individual bot drawdowns: 10 mini gauges
      - Portfolio drawdown: 1 large gauge
      - Color zones: Green 0-10%, Yellow 10-20%, Orange 20-30%, Red 30-40%
      - Needle position: Current drawdown
      - Alert thresholds marked: 25% (bot), 40% (portfolio)
      
      Q4: Consecutive Loss Tracker (Bottom-right):
      Table + visual indicators:
      | Bot | Current Streak | Max Streak | Status | Last Win | Actions |
      |-----|----------------|------------|--------|----------|---------|
      | 8   | 0 wins (🟢)    | 2 losses   | OK     | 15m ago  | -       |
      | 3   | 2 losses (🟡)  | 2 losses   | WARN   | 3h ago   | -       |
      | 7   | 3 losses (🔴)  | 3 losses   | HALT   | 8h ago   | [Resume in 16h] |
      
      Color: 🟢 0-1 losses, 🟡 2 losses (warning), 🔴 3 losses (halted)
      
      Risk Alerts Panel (bottom full-width):
      Live feed of risk events (last 50):
      [21:45:18] ⚠️ WARNING: Bot 3 approaching Zone 4 limit (8.5% / 10%)
      [21:40:32] 🔴 CRITICAL: Bot 7 circuit breaker OPEN - 3 consecutive losses
      [21:35:44] 🟢 INFO: Bot 8 drawdown recovered to 6.2% (was 12.1%)
      [21:30:00] ⚠️ WARNING: Portfolio drawdown 22.3% (threshold 40%)
      
   7. ⚙️ Settings (src/dashboard/pages/7_⚙️_Settings.py):
      
      Tab 1: Global Configuration
      - Risk Management:
        * Max drawdown individual: [25]% [slider]
        * Max drawdown portfolio: [40]% [slider]
        * Circuit breaker consecutive losses: [3] [input]
        * Daily loss limit: [5]% [slider]
        * Kelly fraction: [Half Kelly ▼] [dropdown: Full/Half/Quarter]
      
      - Capital Allocation:
        * Total capital: [$50,000] [input]
        * Emergency reserve: [10]% [slider]
        * Per-bot allocation: [Edit Matrix] [button → modal]
      
      - API Configuration:
        * Polymarket API Key: [••••••••••] [Show/Hide] [Rotate] [Test Connection]
        * Polygon RPC URL: [https://...](https://...) [input] [Test]
        * News APIs: [Enabled ✓] [Configure...]
        * Esports APIs: [Enabled ✓] [Configure...]
      
      - Wallet Settings:
        * Hot wallet address: [0x1234...] [view on Polygonscan]
        * Hot wallet balance: [USDC: $5,234 | MATIC: 12.4]
        * Auto-rebalance threshold: [5]% [slider]
        * Gas price strategy: [Adaptive ▼] [dropdown: Fast/Standard/Adaptive]
        * Max gas price: [100] gwei [input]
      
      Tab 2: Bot-Specific Configuration
      - Bot selector: [Bot 8: Tail Risk + MM ▼]
      - YAML editor: Syntax highlighting, validation on save
      - Actions: [Save] [Reset to Default] [Duplicate from Bot X]
      - Validation results: ✓ Config valid | ✗ Errors: [list]
      
      Tab 3: Notifications
      - Telegram:
        * Enabled: [✓]
        * Bot token: [••••••••••] [input]
        * Chat ID: [123456789] [input]
        * Alert levels: [Critical ✓] [Warning ✓] [Info ✗]
      
      - Discord:
        * Enabled: [✓]
        * Webhook URL: [https://discord.com/api/webhooks/...](https://discord.com/api/webhooks/...) [input]
        * Alert levels: [Critical ✓] [Warning ✓] [Info ✗]
      
      - Email:
        * Enabled: [✗]
        * SMTP server: [...] [input]
        * Recipients: [...] [tags input]
      
      Tab 4: Database Management
      - Database size: 2.4 GB (Last updated: 2m ago) [Refresh]
      - Hypertable stats:
        * orders: 1.2M rows, 850 MB, compression: 4.2x
        * positions: 45K rows, 120 MB, compression: 3.8x
        * trades: 1.1M rows, 620 MB, compression: 4.5x
      
      - Actions:
        * [Run VACUUM] [Reindex Tables] [Update Statistics]
        * [Backup Database] [Restore from Backup] [View Backups]
        * [Archive Old Data] (data >90 days → cold storage)
      
      - Query Performance:
        * Slow queries (>100ms): [View Log]
        * Missing indexes: [None detected ✓]
        * Table bloat: [2.1% (acceptable)]
      
      Tab 5: System Health
      - Service Status:
        * WebSocket Gateway: [🟢 Healthy] [Restart]
        * Market Data Processor: [🟢 Healthy] [Restart]
        * Order Execution Engine: [🟢 Healthy] [Restart]
        * Risk Manager: [🟢 Healthy] [Restart]
        * TimescaleDB: [🟢 Healthy] [Connection: 8/10 pool]
        * Redis: [🟢 Healthy] [Memory: 234MB / 2GB]
      
      - Resource Usage:
        * CPU: [23%] [sparkline chart]
        * Memory: [4.2 GB / 16 GB] [bar chart]
        * Disk: [48 GB / 200 GB] [bar chart]
        * Network: [↑ 12 Mbps ↓ 8 Mbps]
      
      - Logs:
        * Service: [All ▼] Level: [All ▼] Search: [...] [Filter]
        * Live log viewer (auto-scroll, last 500 lines)
        * [Download Logs] [Clear Logs]
   
   DASHBOARD COMPONENTES REUTILIZABLES (src/dashboard/components/):
   - control_panel.py: Emergency controls widget
   - metrics_cards.py: KPI card component (title, value, delta, sparkline)
   - pnl_chart.py: Plotly real-time line chart with annotations
   - position_table.py: Sortable, filterable table with actions
   - order_log_table.py: Paginated table with color coding
   - zone_heatmap.py: 5xN grid heatmap with tooltips
   - latency_monitor.py: Histogram + p50/p95/p99 indicators
   - circuit_breaker_status.py: Status card grid
   - bot_status_grid.py: Bot list with inline controls
   - risk_gauge.py: Speedometer-style gauge chart
   - alert_feed.py: Live scrolling alert feed
   - yaml_editor.py: Code editor with syntax highlighting (ACE editor)
   
   DASHBOARD UTILITIES (src/dashboard/utils/):
   - websocket_client.py: WebSocket client para real-time updates desde API
   - api_client.py: Async HTTP client wrapper para internal API
   - theme.py: Dark minimalist theme (background: #0E1117, accent: #00D9FF)
   - formatters.py: Format numbers ($1,234.50), percentages (12.5%), durations (2h 15m)
   - session_state.py: Streamlit session state manager
   - chart_builder.py: Factory para crear charts consistentes (Plotly templates)
   - data_cache.py: Cache decorator para data fetching (TTL-based)

BOTS LAYER (src/bots/) - STRATEGY PATTERN + STATE MACHINE
   BaseBotStrategy (ABC) (src/bots/base_bot.py):
   - Abstract methods:
     * async def initialize(config: BotConfig) -> None
     * async def execute_cycle(market_data: MarketDataDTO) -> List[OrderDTO]
     * async def stop_gracefully() -> None
     * def get_state() -> BotState
     * def get_metrics() -> BotMetricsDTO
   
   - Implemented methods:
     * start() -> None: State transition IDLE → STARTING → ACTIVE
     * pause() -> None: State transition ACTIVE → PAUSED
     * resume() -> None: State transition PAUSED → ACTIVE
     * stop() -> None: State transition * → STOPPING → STOPPED
     * emergency_halt() -> None: State transition * → EMERGENCY_HALT
     * _validate_state_transition(from, to) -> bool
     * _emit_state_change_event(old, new) -> None
   
   - Integrated features:
     * Logging: Structured JSON logger con bot_id context
     * Metrics: Prometheus metrics (trades_total, pnl, latency)
     * Health checks: Periodic self-check (override in subclass)
     * Error recovery: Catch exceptions, log, emit event, transition to ERROR state
   
   Concrete Bot Strategies (src/bots/bot_01_*.py ... bot_10_*.py):
   - Each bot extends BaseBotStrategy
   - Each bot has specific execute_cycle() logic
   - Each bot has corresponding YAML config in config/bots/
   
   BotOrchestrator (src/bots/bot_manager.py):
   - Manages lifecycle de múltiples bots
   - Dependency injection: Inyecta repositories, services, event bus
   - Start/stop/pause/resume individual o múltiples bots
   - Emergency halt all: Close positions, stop all bots, emit event
   - Health monitoring: Periodic checks, restart si unhealthy
   
   BotFactory (src/bots/bot_factory.py):
   - create(bot_id: int, config: BotConfig) -> BaseBotStrategy
   - Returns correct bot instance basado en bot_id
   - Injects dependencies via constructor
   - Validates config antes de crear bot

═══════════════════════════════════════════════════════════════════════════════
💰 WALLET MANAGEMENT (COMPREHENSIVE)
═══════════════════════════════════════════════════════════════════════════════

WALLET ARCHITECTURE (src/infrastructure/wallet/)

1. WalletManager (wallet_manager.py):
   Responsibilities:
   - Mantener 2 wallets: Hot (trading) + Cold (storage)
   - Auto-rebalance: Transfer cold → hot si balance <threshold
   - Balance tracking: USDC (trading) + MATIC (gas)
   - Nonce management: Thread-safe nonce tracking con Redis locks
   - Transaction signing: Local signing, nunca enviar private key
   - Transaction submission: Submit a Polygon, wait confirmation
   - Transaction tracking: Monitor status, handle failures
   
   Hot Wallet Strategy:
   - Purpose: Active trading, rápido acceso
   - Balance target: 10-20% total capital ($5K-10K si $50K total)
   - Min threshold: 5% capital ($2.5K si $50K total)
   - Max threshold: 25% capital ($12.5K si $50K total)
   - Rebalance trigger: Balance <5% → Transfer cold → hot
   - Rebalance amount: Bring to 15% (mid-point)
   
   Cold Wallet Strategy:
   - Purpose: Secure storage, mayoría capital
   - Balance target: 80-90% total capital
   - Access: Manual intervention required (multi-sig futuro)
   - Transfer out: Only to hot wallet or external (withdrawal)
   
   Methods:
   - get_hot_balance() -> WalletBalanceDTO
   - get_cold_balance() -> WalletBalanceDTO
   - check_rebalance_needed() -> bool
   - auto_rebalance() -> TxHash (transfer cold → hot)
   - manual_withdrawal(amount, destination) -> TxHash
   - get_nonce(address) -> int (with lock)
   - increment_nonce(address) -> None
   - sign_transaction(tx_data, private_key) -> SignedTx
   - submit_transaction(signed_tx) -> TxHash
   - wait_for_confirmation(tx_hash, timeout=60s) -> TxReceipt

2. GasManager (gas_manager.py):
   Responsibilities:
   - Monitor gas prices: Fetch from Polygon Gas Station API
   - Adaptive gas pricing: Select tier based on current prices
   - Gas spike protection: Queue transactions if gas >threshold
   - Gas cost tracking: Log gas spent per bot for ROI calculation
   - Gas estimation: Estimate gas limit for transactions
   - Gas optimization: Batch transactions, use EIP-1559
   
   Gas Price Tiers:
   - Rapid: <30 gwei → Use 'rapid' tier (confirmation <5s)
   - Fast: 30-50 gwei → Use 'fast' tier (confirmation <30s)
   - Standard: 50-100 gwei → Use 'standard' tier (confirmation <2min)
   - High: >100 gwei → QUEUE transactions, alert user, wait for drop
   
   EIP-1559 Parameters:
   - maxPriorityFeePerGas: 30 gwei (tip to miner)
   - maxFeePerGas: base_fee + 30 gwei (max willing to pay)
   - Dynamic adjustment: If transaction pending >2min, bump by 10%
   
   Gas Limits (conservative estimates):
   - USDC transfer: 65,000 (actual ~50K)
   - USDC approve: 50,000 (actual ~45K)
   - Polymarket order: 150,000 (actual ~120K)
   - Polymarket cancel: 80,000 (actual ~60K)
   
   Gas Cost Tracking:
   - Log every transaction: tx_hash, gas_used, gas_price, cost_matic, cost_usdc
   - Aggregate por bot: total_gas_spent_usdc
   - Include en ROI calculation: net_pnl = gross_pnl - gas_costs - trading_fees
   
   Methods:
   - get_current_gas_price() -> GasPriceDTO (rapid, fast, standard)
   - select_gas_tier(urgency: Urgency) -> GasTier
   - estimate_gas(tx_data) -> int
   - calculate_gas_cost_usdc(gas_used, gas_price) -> Decimal
   - should_queue_transaction(current_gas_price) -> bool
   - track_gas_spent(bot_id, tx_hash, gas_cost) -> None
   - get_bot_gas_spent(bot_id) -> Decimal

3. NonceManager (nonce_manager.py):
   Responsibilities:
   - Track nonce per wallet address
   - Thread-safe nonce access (Redis locks)
   - Handle nonce gaps (if transaction fails)
   - Sync with blockchain periodically
   - Prevent nonce collisions (múltiples bots usando mismo wallet)
   
   Implementation:
   - Redis key: nonce:{wallet_address} → current nonce
   - Redis lock: nonce_lock:{wallet_address} → 5s TTL
   - Acquire lock before getting/incrementing nonce
   - Release lock after transaction submitted
   - If lock expires, next caller re-syncs nonce from blockchain
   
   Nonce Sync Strategy:
   - On startup: Fetch nonce from blockchain (web3.eth.get_transaction_count)
   - Every 5min: Re-sync nonce (detect gaps from external txs)
   - On error: If nonce error, force re-sync
   
   Methods:
   - get_nonce(address: str) -> int (with lock)
   - increment_nonce(address: str) -> None
   - sync_nonce_from_blockchain(address: str) -> int
   - reset_nonce(address: str, nonce: int) -> None

4. WalletRecovery (wallet_recovery.py):
   Responsibilities:
   - Backup mnemonic phrase (encrypted)
   - Recover wallet from mnemonic
   - Emergency withdrawal (if bot compromised)
   - Wallet rotation (change wallet without downtime)
   
   Mnemonic Backup:
   - Generate: 24-word BIP39 mnemonic (high entropy)
   - Encrypt: AES-256-GCM with password-derived key (PBKDF2)
   - Store: Encrypted file on cold storage (USB, offline machine)
   - Never store plain mnemonic on hot machine
   
   Recovery Process:
   1. User provides encrypted mnemonic file + password
   2. Decrypt mnemonic
   3. Derive private key (BIP44 path: m/44'/60'/0'/0/0)
   4. Verify address matches expected
   5. Load wallet into system
   
   Emergency Withdrawal:
   - Trigger: Manual action si bot compromised o critical bug
   - Action: Transfer ALL funds (USDC + MATIC) to cold wallet
   - Priority: Use 'rapid' gas tier (ignore cost)
   - Notification: Send urgent alert (Telegram, Discord, Email)
   
   Wallet Rotation:
   - Use case: Change hot wallet periodically for security
   - Process:
     1. Generate new hot wallet
     2. Transfer funds old → new
     3. Update config con new address
     4. Restart bots con new wallet
     5. Archive old wallet (keep for audit trail)
   
   Methods:
   - backup_mnemonic(mnemonic, password, filepath) -> None
   - restore_from_mnemonic(encrypted_file, password) -> Wallet
   - emergency_withdraw_all(destination_address) -> TxHash
   - rotate_wallet(new_address, new_private_key) -> None

5. WalletMonitor (wallet_monitor.py):
   Responsibilities:
   - Monitor balances (USDC, MATIC)
   - Alert si balance bajo
   - Track pending transactions
   - Detect stuck transactions
   - Auto-bump gas si transaction pending >threshold
   
   Balance Monitoring:
   - Check every 30s: Hot wallet USDC balance
   - Check every 60s: Hot wallet MATIC balance
   - Alert thresholds:
     * USDC <$2,500 (5% of $50K): WARNING
     * USDC <$1,000 (2% of $50K): CRITICAL, trigger auto-rebalance
     * MATIC <5: WARNING (low gas funds)
     * MATIC <2: CRITICAL, alert user to top up
   
   Pending Transaction Monitoring:
   - Track all submitted transactions: tx_hash, submit_time, status
   - Check status every 15s
   - If pending >2min: Bump gas by 10%
   - If pending >5min: Bump gas by 20%, alert user
   - If pending >10min: Mark as stuck, manual intervention
   
   Methods:
   - monitor_balances() -> None (continuous loop)
   - check_balance_thresholds(balance) -> AlertLevel
   - monitor_pending_transactions() -> None (continuous loop)
   - bump_transaction_gas(tx_hash, bump_percent) -> TxHash
   - handle_stuck_transaction(tx_hash) -> None

WALLET SECURITY BEST PRACTICES:
✓ Never log private keys (even in debug mode)
✓ Never send private keys over network
✓ Encrypt private keys at rest (AES-256)
✓ Use environment variables for secrets (never hardcode)
✓ Rotate wallets periodically (every 90 days)
✓ Multi-sig for cold wallet (future enhancement)
✓ Hardware wallet support (Ledger/Trezor) for cold wallet (future)
✓ Rate limit wallet operations (prevent abuse)
✓ Monitor for suspicious activity (unusual withdrawals)
✓ Keep audit trail (all transactions logged)

WALLET ERROR HANDLING:
- InsufficientBalanceError: Auto-rebalance si hot wallet, alert si cold wallet
- InsufficientGasError: Alert user to top up MATIC
- NonceOutOfSyncError: Force re-sync from blockchain
- TransactionFailedError: Log, emit event, retry con higher gas
- TransactionStuckError: Bump gas, alert user si persiste
- WalletLockedError: Emergency halt, require manual unlock

═══════════════════════════════════════════════════════════════════════════════
🗄️ DATABASE OPTIMIZATION (TIMESCALEDB TUNING)
═══════════════════════════════════════════════════════════════════════════════

TIMESCALEDB SCHEMA (src/infrastructure/persistence/schema.sql)

Hypertables (automatic time-based partitioning):

1. orders (partition by timestamp, 7-day chunks):
   CREATE TABLE orders (
       order_id UUID PRIMARY KEY,
       bot_id INTEGER NOT NULL,
       market_id VARCHAR(66) NOT NULL,
       side VARCHAR(3) NOT NULL CHECK (side IN ('YES', 'NO')),
       size DECIMAL(20, 6) NOT NULL CHECK (size > 0),
       price DECIMAL(10, 8) NOT NULL CHECK (price >= 0.01 AND price <= 0.99),
       zone INTEGER NOT NULL CHECK (zone BETWEEN 1 AND 5),
       order_type VARCHAR(10) NOT NULL CHECK (order_type IN ('POST', 'TAKE')),
       status VARCHAR(20) NOT NULL,
       created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       filled_at TIMESTAMPTZ,
       canceled_at TIMESTAMPTZ,
       fees_paid DECIMAL(20, 6),
       slippage DECIMAL(10, 4)
   );
   
   SELECT create_hypertable('orders', 'created_at', chunk_time_interval => INTERVAL '7 days');
   
   Indices:
   CREATE INDEX idx_orders_bot_timestamp ON orders (bot_id, created_at DESC);
   CREATE INDEX idx_orders_market ON orders (market_id, created_at DESC);
   CREATE INDEX idx_orders_status ON orders (status, created_at DESC) WHERE status IN ('PENDING', 'PARTIALLY_FILLED');
   CREATE INDEX idx_orders_zone ON orders (zone, created_at DESC);
   
   Compression (after 14 days):
   ALTER TABLE orders SET (
       timescaledb.compress,
       timescaledb.compress_segmentby = 'bot_id',
       timescaledb.compress_orderby = 'created_at DESC'
   );
   SELECT add_compression_policy('orders', INTERVAL '14 days');
   
   Retention (delete after 365 days):
   SELECT add_retention_policy('orders', INTERVAL '365 days');

2. positions (partition by opened_at, 7-day chunks):
   CREATE TABLE positions (
       position_id UUID PRIMARY KEY,
       bot_id INTEGER NOT NULL,
       order_id UUID NOT NULL REFERENCES orders(order_id),
       market_id VARCHAR(66) NOT NULL,
       side VARCHAR(3) NOT NULL,
       size DECIMAL(20, 6) NOT NULL,
       entry_price DECIMAL(10, 8) NOT NULL,
       current_price DECIMAL(10, 8),
       realized_pnl DECIMAL(20, 6),
       unrealized_pnl DECIMAL(20, 6),
       zone INTEGER NOT NULL,
       opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       closed_at TIMESTAMPTZ,
       hold_duration INTERVAL GENERATED ALWAYS AS (closed_at - opened_at) STORED
   );
   
   SELECT create_hypertable('positions', 'opened_at', chunk_time_interval => INTERVAL '7 days');
   
   Indices:
   CREATE INDEX idx_positions_bot_open ON positions (bot_id, opened_at DESC) WHERE closed_at IS NULL;
   CREATE INDEX idx_positions_bot_closed ON positions (bot_id, closed_at DESC) WHERE closed_at IS NOT NULL;
   CREATE INDEX idx_positions_market ON positions (market_id, opened_at DESC);
   
   Compression (after 14 days):
   ALTER TABLE positions SET (
       timescaledb.compress,
       timescaledb.compress_segmentby = 'bot_id',
       timescaledb.compress_orderby = 'opened_at DESC'
   );
   SELECT add_compression_policy('positions', INTERVAL '14 days');
   
   Retention (delete after 365 days):
   SELECT add_retention_policy('positions', INTERVAL '365 days');

3. trades (partition by executed_at, 7-day chunks):
   CREATE TABLE trades (
       trade_id UUID PRIMARY KEY,
       order_id UUID NOT NULL REFERENCES orders(order_id),
       bot_id INTEGER NOT NULL,
       market_id VARCHAR(66) NOT NULL,
       executed_price DECIMAL(10, 8) NOT NULL,
       executed_size DECIMAL(20, 6) NOT NULL,
       fees_paid DECIMAL(20, 6) NOT NULL,
       slippage DECIMAL(10, 4),
       gas_cost_usdc DECIMAL(20, 6),
       executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
   );
   
   SELECT create_hypertable('trades', 'executed_at', chunk_time_interval => INTERVAL '7 days');
   
   Indices:
   CREATE INDEX idx_trades_bot_timestamp ON trades (bot_id, executed_at DESC);
   CREATE INDEX idx_trades_order ON trades (order_id, executed_at DESC);
   
   Compression (after 14 days):
   ALTER TABLE trades SET (
       timescaledb.compress,
       timescaledb.compress_segmentby = 'bot_id',
       timescaledb.compress_orderby = 'executed_at DESC'
   );
   SELECT add_compression_policy('trades', INTERVAL '14 days');

4. market_snapshots (partition by snapshot_at, 1-day chunks):
   CREATE TABLE market_snapshots (
       snapshot_id BIGSERIAL,
       market_id VARCHAR(66) NOT NULL,
       yes_price DECIMAL(10, 8) NOT NULL,
       no_price DECIMAL(10, 8) NOT NULL,
       liquidity DECIMAL(20, 6),
       volume_24h DECIMAL(20, 6),
       snapshot_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       PRIMARY KEY (snapshot_id, snapshot_at)
   );
   
   SELECT create_hypertable('market_snapshots', 'snapshot_at', chunk_time_interval => INTERVAL '1 day');
   
   Indices:
   CREATE INDEX idx_market_snapshots_market ON market_snapshots (market_id, snapshot_at DESC);
   
   Compression (after 7 days):
   ALTER TABLE market_snapshots SET (
       timescaledb.compress,
       timescaledb.compress_segmentby = 'market_id',
       timescaledb.compress_orderby = 'snapshot_at DESC'
   );
   SELECT add_compression_policy('market_snapshots', INTERVAL '7 days');
   
   Retention (delete after 90 days):
   SELECT add_retention_policy('market_snapshots', INTERVAL '90 days');

CONTINUOUS AGGREGATES (materialized views with automatic refresh):

1. bot_performance_hourly:
   CREATE MATERIALIZED VIEW bot_performance_hourly
   WITH (timescaledb.continuous) AS
   SELECT
       time_bucket('1 hour', executed_at) AS hour,
       bot_id,
       COUNT(*) AS trades_count,
       SUM(executed_size * executed_price) AS volume_usdc,
       SUM(fees_paid) AS total_fees,
       SUM(gas_cost_usdc) AS total_gas_cost,
       AVG(slippage) AS avg_slippage
   FROM trades
   GROUP BY hour, bot_id;
   
   SELECT add_continuous_aggregate_policy('bot_performance_hourly',
       start_offset => INTERVAL '3 hours',
       end_offset => INTERVAL '1 hour',
       schedule_interval => INTERVAL '1 hour'
   );

2. bot_pnl_daily:
   CREATE MATERIALIZED VIEW bot_pnl_daily
   WITH (timescaledb.continuous) AS
   SELECT
       time_bucket('1 day', closed_at) AS day,
       bot_id,
       COUNT(*) AS positions_closed,
       SUM(realized_pnl) AS total_realized_pnl,
       AVG(realized_pnl) AS avg_pnl_per_position,
       SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END)::DECIMAL / COUNT(*) AS win_rate,
       AVG(EXTRACT(EPOCH FROM hold_duration) / 3600) AS avg_hold_hours
   FROM positions
   WHERE closed_at IS NOT NULL
   GROUP BY day, bot_id;
   
   SELECT add_continuous_aggregate_policy('bot_pnl_daily',
       start_offset => INTERVAL '3 days',
       end_offset => INTERVAL '1 day',
       schedule_interval => INTERVAL '1 day'
   );

3. market_price_5min:
   CREATE MATERIALIZED VIEW market_price_5min
   WITH (timescaledb.continuous) AS
   SELECT
       time_bucket('5 minutes', snapshot_at) AS time,
       market_id,
       FIRST(yes_price, snapshot_at) AS open_yes,
       MAX(yes_price) AS high_yes,
       MIN(yes_price) AS low_yes,
       LAST(yes_price, snapshot_at) AS close_yes,
       AVG(liquidity) AS avg_liquidity
   FROM market_snapshots
   GROUP BY time, market_id;
   
   SELECT add_continuous_aggregate_policy('market_price_5min',
       start_offset => INTERVAL '1 hour',
       end_offset => INTERVAL '5 minutes',
       schedule_interval => INTERVAL '5 minutes'
   );

QUERY OPTIMIZATION TECHNIQUES:

1. Partition Pruning:
   ✓ Always include timestamp in WHERE clause
   ✓ Example: WHERE created_at >= NOW() - INTERVAL '7 days'
   → TimescaleDB only scans relevant chunks (7 days), not entire table

2. Index Usage:
   ✓ Create covering indices para common queries
   ✓ Use INCLUDE clause para index-only scans
   ✓ Example: CREATE INDEX idx_orders_bot_cover ON orders (bot_id, created_at DESC) INCLUDE (status, size, price);

3. Continuous Aggregates:
   ✓ Pre-compute expensive aggregations
   ✓ Query aggregates instead of raw data
   ✓ Example: SELECT * FROM bot_pnl_daily WHERE day >= NOW() - INTERVAL '30 days' AND bot_id = 8;
   → Fast (materialized view) vs slow (scan millions of positions)

4. Compression:
   ✓ Automatic compression after 14 days reduces storage 4-5x
   ✓ Compressed data still queryable (transparent decompression)
   ✓ Trade-off: Slower queries on compressed chunks (acceptable for old data)

5. Connection Pooling:
   ✓ Use asyncpg connection pool (10 connections)
   ✓ Reuse connections, avoid connect overhead
   ✓ Example: pool = await asyncpg.create_pool(dsn, min_size=5, max_size=10)

6. Prepared Statements:
   ✓ Prepare frequently-used queries
   ✓ Reduce parsing overhead
   ✓ Example: stmt = await conn.prepare('SELECT * FROM orders WHERE bot_id = $1 ORDER BY created_at DESC LIMIT $2')

7. EXPLAIN ANALYZE:
   ✓ Always EXPLAIN ANALYZE slow queries (>100ms)
   ✓ Identify sequential scans (add index), sort operations (use index order)
   ✓ Target: Index scan, <10ms for simple queries, <100ms for aggregations

MAINTENANCE TASKS (automated via pg_cron):

1. VACUUM (daily at 2 AM):
   SELECT cron.schedule('vacuum-daily', '0 2 * * *', 'VACUUM ANALYZE');
   → Reclaims storage, updates statistics

2. REINDEX (weekly on Sunday 3 AM):
   SELECT cron.schedule('reindex-weekly', '0 3 * * 0', 'REINDEX DATABASE pets');
   → Rebuilds indices, removes bloat

3. UPDATE STATISTICS (daily at 1 AM):
   SELECT cron.schedule('stats-daily', '0 1 * * *', 'ANALYZE');
   → Updates query planner statistics

4. BACKUP (every 6 hours):
   SELECT cron.schedule('backup-6h', '0 */6 * * *', 'pg_dump pets | gzip > /backups/pets_$(date +\%Y\%m\%d_\%H\%M).sql.gz');
   → Creates compressed backup

5. ARCHIVE OLD DATA (monthly on 1st at 4 AM):
   SELECT cron.schedule('archive-monthly', '0 4 1 * *', 'SELECT archive_old_data()');
   → Moves data >365 days to cold storage (S3/Glacier)

DATABASE MONITORING (via Prometheus postgres_exporter):
   - pg_stat_database: Connections, transactions, conflicts
   - pg_stat_activity: Active queries, long-running queries
   - pg_stat_user_tables: Table sizes, bloat, last vacuum
   - pg_stat_user_indexes: Index sizes, usage, scans
   - TimescaleDB-specific: Chunk sizes, compression ratios, hypertable stats

PERFORMANCE TARGETS:
   ✓ Simple queries (<10 results): <10ms p99
   ✓ Aggregation queries (hourly/daily stats): <50ms p99
   ✓ Dashboard queries (last 24h data): <100ms p99
   ✓ Full table scans: NEVER (always use indices + partition pruning)
   ✓ Connection checkout: <5ms p99
   ✓ Write latency: <10ms p99 (async writes via connection pool)

═══════════════════════════════════════════════════════════════════════════════
💻 CÓDIGO ULTRA-PROFESIONAL (EXCELENCIA DESDE PRIMERA ITERACIÓN)
═══════════════════════════════════════════════════════════════════════════════

TYPE SAFETY (MYPY STRICT MODE - ENFORCEMENT ABSOLUTO):
   ✓ mypy.ini:
     [mypy]
     python_version = 3.11
     strict = True
     warn_return_any = True
     warn_unused_configs = True
     disallow_untyped_defs = True
     disallow_any_unimported = True
     no_implicit_optional = True
     warn_redundant_casts = True
     warn_unused_ignores = True
     warn_no_return = True
     check_untyped_defs = True
     strict_equality = True
   
   ✓ Every function MUST have type hints:
     def calculate_kelly(p: float, odds: float, capital: Decimal) -> Decimal:
         ...
   
   ✗ PROHIBITED: Any type, untyped functions, implicit Optional

DOCSTRINGS (GOOGLE STYLE - OBLIGATORIO):
   """Brief one-line description.
   
   Longer description explaining purpose, algorithm, edge cases.
   Can span multiple lines with examples and mathematical formulas.
   
   Args:
       param1: Description of param1 with type context if needed
       param2: Description of param2, explain constraints
       param3: Optional param, explain default behavior
   
   Returns:
       Description of return value with type context
       Explain what None means if Optional
   
   Raises:
       ValueError: When param1 is negative
       OrderRejectedError: When Polymarket rejects order, include reason
   
   Example:
       >>> result = function(arg1=10, arg2="test")
       >>> assert result == expected_value
   
   Note:
       Additional notes about performance, complexity, limitations
   
   References:
       [1] Paper/article if complex algorithm
       [2] External documentation link
   """

ERROR HANDLING (RESULT TYPE PATTERN):
   from typing import Generic, TypeVar, Union
   from dataclasses import dataclass
   
   T = TypeVar('T')
   E = TypeVar('E')
   
   @dataclass(frozen=True)
   class Ok(Generic[T]):
       value: T
   
   @dataclass(frozen=True)
   class Err(Generic[E]):
       error: E
   
   Result = Union[Ok[T], Err[E]]
   
   def place_order(order: Order) -> Result[OrderId, OrderError]:
       try:
           validated = validate_order(order)
           if isinstance(validated, Err):
               return validated
           
           order_id = execute_order(order)
           return Ok(order_id)
       
       except InsufficientBalanceError as e:
           logger.error("insufficient_balance", extra={"order": order, "error": str(e)})
           return Err(OrderError.INSUFFICIENT_BALANCE)
       
       except Exception as e:
           logger.exception("unexpected_error", extra={"order": order})
           return Err(OrderError.UNKNOWN)
   
   # Usage:
   result = place_order(order)
   match result:
       case Ok(order_id):
           logger.info("order_placed", extra={"order_id": order_id})
           return order_id
       case Err(error):
           logger.error("order_failed", extra={"error": error})
           raise OrderExecutionError(error)

LOGGING (STRUCTURED JSON):
   import logging
   import json
   from datetime import datetime
   
   class JSONFormatter(logging.Formatter):
       def format(self, record):
           log_data = {
               'timestamp': datetime.utcnow().isoformat() + 'Z',
               'level': record.levelname,
               'service': 'pets',
               'component': record.name,
               'message': record.getMessage(),
               'correlation_id': getattr(record, 'correlation_id', None),
               **record.__dict__.get('extra', {})
           }
           
           if record.exc_info:
               log_data['exception'] = self.formatException(record.exc_info)
           
           return json.dumps(log_data)
   
   # Usage:
   logger.info(
       "order_placed",
       extra={
           'bot_id': 8,
           'order_id': str(order.id),
           'market_id': order.market_id,
           'side': order.side.value,
           'size': float(order.size),
           'price': float(order.price),
           'zone': order.zone,
           'correlation_id': request_context.correlation_id
       }
   )

ASYNC/AWAIT (CORRECTO):
   import asyncio
   from typing import List
   
   async def fetch_multiple_markets(market_ids: List[str]) -> List[Market]:
       """Fetch multiple markets concurrently."""
       tasks = [fetch_market(mid) for mid in market_ids]
       results = await asyncio.gather(*tasks, return_exceptions=True)
       
       markets = []
       for i, result in enumerate(results):
           if isinstance(result, Exception):
               logger.error("fetch_failed", extra={"market_id": market_ids[i], "error": str(result)})
           else:
               markets.append(result)
       
       return markets
   
   async def rate_limited_operation(semaphore: asyncio.Semaphore, operation, *args):
       """Execute operation with rate limiting."""
       async with semaphore:
           return await operation(*args)
   
   # Usage:
   semaphore = asyncio.Semaphore(10)  # Max 10 concurrent
   tasks = [rate_limited_operation(semaphore, fetch_market, mid) for mid in market_ids]
   results = await asyncio.gather(*tasks)

INPUT VALIDATION (PYDANTIC V2):
   from pydantic import BaseModel, Field, field_validator, model_validator
   from decimal import Decimal
   from typing import Literal
   
   class OrderRequest(BaseModel):
       market_id: str = Field(..., pattern=r'^0x[a-f0-9]{64}$')
       side: Literal['YES', 'NO']
       size: Decimal = Field(..., gt=0, le=10000, decimal_places=6)
       price: Decimal = Field(..., ge=Decimal('0.01'), le=Decimal('0.99'), decimal_places=8)
       bot_id: int = Field(..., ge=1, le=10)
       post_only: bool = True
       
       @field_validator('price')
       @classmethod
       def validate_zone_restrictions(cls, v, info):
           if Decimal('0.60') <= v <= Decimal('0.98'):
               raise ValueError('Directional bets prohibited in Zone 4-5')
           return v
       
       @model_validator(mode='after')
       def validate_size_for_zone(self):
           zone = classify_zone(self.price)
           if zone == 1 and self.size > 500:
               raise ValueError('Max size 500 for Zone 1 (tail risk)')
           return self
       
       model_config = {
           'strict': True,
           'frozen': True
       }

CODE ORGANIZATION (MODULES):
   """
   Module: Kelly Criterion Calculator
   
   Implements Half Kelly and Quarter Kelly position sizing for optimal growth
   with reduced variance. Handles edge cases and validates inputs rigorously.
   
   References:
       [1] Kelly, J. L. (1956). "A New Interpretation of Information Rate"
       [2] Thorp, E. O. (2006). "The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market"
   """
   
   from __future__ import annotations
   
   # Standard library
   import logging
   from decimal import Decimal, ROUND_HALF_UP
   from typing import Protocol
   
   # Third-party
   from pydantic import BaseModel, Field
   
   # Local
   from pets.domain.value_objects import Price
   from pets.domain.exceptions import InvalidProbabilityError, InvalidOddsError
   
   # Constants
   MIN_EDGE = Decimal('0.05')  # 5% minimum edge required
   MAX_KELLY_FRACTION = Decimal('0.5')  # Half Kelly max
   
   # Public API
   __all__ = ['KellyCalculator', 'calculate_kelly_fraction', 'KellyResult']
   
   # Logger
   logger = logging.getLogger(__name__)
   
   # Data classes
   class KellyResult(BaseModel):
       fraction: Decimal = Field(..., ge=0, le=1)
       edge: Decimal
       kelly_type: Literal['full', 'half', 'quarter']
       
       model_config = {'frozen': True}
   
   # Implementation
   class KellyCalculator:
       """Calculate Kelly Criterion position sizing."""
       ...

NAMING CONVENTIONS:
   ✓ Classes: PascalCase (OrderRepository, RiskManager)
   ✓ Functions: snake_case (calculate_kelly, place_order)
   ✓ Constants: UPPER_SNAKE_CASE (MAX_DRAWDOWN, ZONE_4_MIN)
   ✓ Private: _leading_underscore (_calculate_internal, _OrderState)
   ✓ Booleans: is_, has_, can_ (is_valid, has_positions, can_trade)
   ✓ Enums: PascalCase members (Side.YES, BotState.ACTIVE)
   ✗ Single-letter vars (except i, j, k in loops)
   ✗ Abbreviations (ord, pos, mkt)

FUNCTIONS (SMALL + PURE):
   async def place_order(
       order: Order,
       executor: OrderExecutor,
       risk_manager: RiskManager,
       event_bus: EventBus
   ) -> OrderId:
       """Place order with risk validation.
       
       Args:
           order: Order to place
           executor: Order executor service
           risk_manager: Risk validation service
           event_bus: Event bus for publishing events
       
       Returns:
           OrderId if successful
       
       Raises:
           RiskViolationError: If order violates risk rules
           OrderRejectedError: If Polymarket rejects order
       """
       # Validate risk
       risk_result = await risk_manager.validate(order)
       if isinstance(risk_result, Err):
           raise RiskViolationError(risk_result.error)
       
       # Execute order
       execution_result = await executor.execute(order)
       if isinstance(execution_result, Err):
           raise OrderRejectedError(execution_result.error)
       
       # Publish event
       await event_bus.publish(OrderPlacedEvent(execution_result.value))
       
       # Log success
       logger.info("order_placed", extra={"order_id": execution_result.value})
       
       return execution_result.value

IMMUTABILITY:
   from dataclasses import dataclass
   from decimal import Decimal
   
   @dataclass(frozen=True)
   class Price:
       value: Decimal
       zone: int
       
       def __post_init__(self):
           if not Decimal('0.01') <= self.value <= Decimal('0.99'):
               raise ValueError(f"Price {self.value} outside valid range")
           
           expected_zone = self._calculate_zone(self.value)
           if self.zone != expected_zone:
               object.__setattr__(self, 'zone', expected_zone)
       
       @staticmethod
       def _calculate_zone(price: Decimal) -> int:
           if price < Decimal('0.20'):
               return 1
           elif price < Decimal('0.40'):
               return 2
           elif price < Decimal('0.60'):
               return 3
           elif price < Decimal('0.80'):
               return 4
           else:
               return 5

COMMENTS (SOLO CUANDO NECESARIO):
   # Calculate Kelly Criterion using Half Kelly formula
   # Formula: f* = (bp - q) / b / 2, where:
   #   b = odds - 1 (net odds)
   #   p = probability of winning
   #   q = 1 - p (probability of losing)
   # Reference: Kelly (1956), Thorp (2006)
   kelly_full = (odds * probability - (1 - probability)) / odds
   kelly_half = kelly_full / Decimal('2')  # Reduce variance
   
   # HACK: Polymarket API occasionally returns 0.0 liquidity for active markets
   # Workaround: Use cached liquidity if API returns 0
   # TODO: Report to Polymarket, remove after fix (ticket #1234)
   if market.liquidity == Decimal('0'):
       logger.warning("zero_liquidity_workaround", extra={"market_id": market.id})
       market.liquidity = cache.get(f"liquidity:{market.id}") or Decimal('1000')

═══════════════════════════════════════════════════════════════════════════════
🎯 ROADMAP DETALLADO (NO MODIFICAR ORDEN)
═══════════════════════════════════════════════════════════════════════════════

FASE 1: ✅ ESTRUCTURA DIRECTORIOS (COMPLETADO)
   Entregables:
   - 52 directorios creados
   - 168 archivos placeholder
   - Git initialized, pushed a GitHub
   - README.md, .gitignore, .env.example
   
   Status: ✅ COMPLETADO

FASE 2: ⏳ ARCHIVOS DE CONFIGURACIÓN (PRIORIDAD ACTUAL)
   Orden EXACTO (NO cambiar):
   
   1. requirements.txt (30 min):
      - Dependencies pinneadas con hashes (pip-compile)
      - Secciones: Core, Database, API, Dashboard, Testing, Dev tools
      - Versiones exactas (no ~=, >=)
   
   2. pyproject.toml (20 min):
      - [tool.black]: line-length = 120, target-version = py311
      - [tool.ruff]: select = ALL, ignore = específicos
      - [tool.mypy]: strict = true, completo
      - [tool.pytest.ini_options]: testpaths, markers
      - [tool.coverage.run]: source = src, omit = tests
   
   3. pytest.ini (10 min):
      - Markers: unit, integration, e2e, slow
      - Addopts: -v, --strict-markers, --cov
      - Timeout: 300s para e2e, 30s para integration, 5s para unit
   
   4. .pre-commit-config.yaml (15 min):
      - Hooks: black, ruff, mypy, pytest (unit only), gitleaks
      - Fail fast en primer error
   
   5. docker-compose.yml (2 horas):
      - 16 services: timescaledb, redis, websocket_gateway, market_data_processor,
        order_execution_engine, risk_manager, bot_01...bot_10, api, dashboard,
        prometheus, grafana
      - Networks: backend, frontend
      - Volumes: timescaledb_data, redis_data, logs
      - Health checks para todos
      - Restart policies: unless-stopped
      - Resource limits: CPU, memory
   
   6. Makefile (1 hora):
      - 25 comandos: setup, start, stop, restart, logs, logs-bot-XX, test,
        test-unit, test-integration, test-e2e, lint, format, type-check,
        build, clean, backup-db, restore-db, shell-db, shell-redis,
        dashboard, grafana, health, deploy-prod, ci
      - Documentación inline para cada comando
   
   ETA: 4-5 horas trabajo enfocado
   Success Criteria:
   - make setup ejecuta sin errores
   - make start levanta todos los 16 services
   - make test ejecuta suite vacía (placeholder tests)
   - make lint pasa (sin código aún, solo estructura)

FASE 3: ⏳ CORE SERVICES (BOTTOM-UP, 1 SEMANA)
   Orden EXACTO (dependencies bottom → top):
   
   Día 1-2: Data Models & Repositories
   1. src/data/models.py (4 horas):
      - SQLAlchemy models: BotModel, OrderModel, PositionModel, TradeModel, MarketModel, WalletModel
      - Pydantic schemas: Todos los DTOs
      - Enums: Side, OrderStatus, BotState, Zone
      - Migrations Alembic: Initial schema
   
   2. src/data/redis_client.py (2 horas):
      - RedisClient class con connection pooling
      - Methods: get, set, delete, publish, subscribe, lock
      - Serialization: JSON + optional gzip
   
   3. src/data/timescaledb.py (3 horas):
      - TimescaleDBClient class con asyncpg pool
      - Create hypertables, add compression policies
      - Repository implementations: OrderRepository, PositionRepository, etc.
   
   Día 3: Event Bus & Wallet
   4. src/core/event_bus.py (2 horas):
      - RedisPubSubEventBus implementation
      - Publish/subscribe domain events
      - Consumer groups support
   
   5. src/infrastructure/wallet/wallet_manager.py (4 horas):
      - WalletManager: hot/cold wallet management
      - Auto-rebalance logic
      - Nonce management con Redis locks
   
   6. src/infrastructure/wallet/gas_manager.py (2 horas):
      - GasManager: monitor gas prices, adaptive pricing
      - Gas spike protection
      - EIP-1559 implementation
   
   Día 4-5: WebSocket & Market Data
   7. src/core/websocket_gateway.py (6 horas):
      - Persistent WebSocket connection to Polymarket
      - Auto-reconnect con exponential backoff
      - Heartbeat monitoring
      - Message broadcasting via Redis Pub/Sub
      - Rate limiting (3,500/10s burst)
   
   8. src/core/market_data_processor.py (4 horas):
      - Process order book messages
      - Calculate spreads, liquidity, volatility
      - Classify price zones
      - Detect arbitrage opportunities (YES+NO≠$1)
      - Aggregate OHLC data
   
   Día 6: Risk Management
   9. src/core/risk_manager.py (6 horas):
      - Implement 5-zone framework with validation
      - Circuit breaker logic (consecutive losses, drawdown)
      - Kelly calculator (Half/Quarter)
      - Zone restriction validator
      - Drawdown monitor
   
   Día 7: Order Execution
   10. src/core/order_execution_engine.py (6 horas):
       - HMAC-SHA256 authentication
       - Post-only order placement
       - Slippage prediction
       - Order fill tracking
       - Retry logic con exponential backoff
       - Gas estimation & payment
   
   ETA: 40 horas (1 semana full-time, 2 semanas part-time)
   Success Criteria:
   - Integration tests pass para cada componente
   - WebSocket receives market data y broadcastea via Redis
   - Risk Manager valida orders correctamente (rechaza Zone 4-5 directional)
   - Order Execution coloca post-only orders en Polymarket testnet
   - Wallet Manager mantiene balance y gestiona nonces
   - Latency <100ms p99 para order flow completo

FASE 4: ⏳ BOT 8 PROTOTYPE (MEJOR EVIDENCIA, 1 SEMANA)
   Razón: Bot 8 tiene mejor evidencia empírica (planktonXD $106K documentado)
   
   Día 1: Base Bot
   1. src/bots/base_bot.py (4 horas):
      - Abstract BaseBotStrategy class
      - State machine implementation
      - Lifecycle methods: start, stop, pause, resume, emergency_halt
      - Integrated logging, metrics, health checks
   
   Día 2-3: Tail Risk Strategy
   2. src/strategies/tail_risk/low_liquidity_scanner.py (3 horas):
      - Scan markets con liquidity <$1K, volume <$500/day
      - Filter by price: 0.1¢ - 5¢ (Zone 1)
   
   3. src/strategies/tail_risk/tail_opportunity_filter.py (3 horas):
      - Validate opportunities: sentiment, time to resolve, category
      - Score opportunities (0-100)
   
   4. src/strategies/tail_risk/portfolio_diversifier.py (2 horas):
      - Diversify across 20-50 positions
      - Max $20-50 per position
      - Balance across categories
   
   Día 4: Market Making Strategy (reuse)
   5. src/strategies/market_making/spread_calculator.py (3 horas):
      - Calculate optimal spread based on volatility
      - Target: 2-5% spread
   
   6. src/strategies/market_making/inventory_manager.py (2 horas):
      - Rebalance inventory every 5-30 min
      - Avoid directional exposure
   
   Día 5-6: Bot 8 Implementation
   7. src/bots/bot_08_tail_risk_combo.py (8 horas):
      - Implement execute_cycle():
        * Scan tail opportunities (5-20 per day)
        * Place MM orders en mercados estables (100-170 per day)
        * Rebalance portfolio cada 1 hora
      - Integrate with core services
      - Error handling, state management
   
   Día 7: Testing & Config
   8. tests/unit/test_bot_08.py (4 horas):
      - Test individual methods
      - Mock dependencies
      - Edge cases: no opportunities, API failures, risk violations
      - Target: ≥85% coverage
   
   9. tests/integration/test_bot_08_integration.py (3 horas):
      - Test full flow con real DB/Redis (testcontainers)
      - Verify orders placed, positions opened, events emitted
   
   10. config/bots/bot_08_tail_risk_combo.yaml (1 hora):
       - Complete configuration
       - Tune parameters based on backtests
   
   ETA: 40 horas (1 semana full-time)
   Success Criteria:
   - Bot 8 ejecuta trades en paper trading mode
   - Win rate >52% en paper trading (2 semanas mínimo)
   - Unit tests ≥85% coverage
   - Integration tests pass
   - No violations de risk management
   - Latency <200ms para ciclo completo

FASE 5: ⏳ DASHBOARD MVP (3-4 DÍAS)
   Orden EXACTO:
   
   Día 1: Infrastructure
   1. src/dashboard/app.py (2 horas):
      - Streamlit setup, navigation, theme
      - WebSocket connection a API
      - Session state management
   
   2. src/dashboard/utils/websocket_client.py (2 horas):
      - WebSocket client para real-time updates
      - Reconnection logic
   
   3. src/dashboard/utils/api_client.py (2 horas):
      - Async HTTP client wrapper
      - Error handling, retries
   
   Día 2: Core Components
   4. src/dashboard/components/control_panel.py (2 horas):
      - Emergency controls
      - Bot start/stop/pause buttons
   
   5. src/dashboard/components/metrics_cards.py (2 horas):
      - KPI cards component
      - Real-time updates (1s refresh)
   
   6. src/dashboard/components/pnl_chart.py (3 horas):
      - Plotly real-time line chart
      - 10 bot lines, annotations
   
   Día 3: Pages
   7. src/dashboard/pages/1_🏠_Overview.py (3 horas):
      - Layout con metrics + charts
      - Emergency controls integration
   
   8. src/dashboard/pages/2_🤖_Bot_Control.py (3 horas):
      - Bot grid + detail panel
      - Individual bot controls
   
   Día 4: Testing & Polish
   9. src/dashboard/pages/4_💰_Positions.py (2 horas):
      - Active positions table
      - Close position actions
   
   10. Polish & testing (3 horas):
       - Test all interactions
       - Fix bugs, improve UX
       - Dark theme refinement
   
   ETA: 28 horas (3-4 días)
   Success Criteria:
   - Dashboard accesible en localhost:8501
   - Real-time metrics update cada 1s
   - Bot controls funcionan (start/stop Bot 8)
   - P&L chart muestra datos reales
   - No errores en console

FASE 6: ⏳ PAPER TRADING (4 SEMANAS PARALELO)
   Mientras desarrollas resto:
   1. Ejecutar Bot 8 en paper trading mode
   2. Monitorear métricas diarias
   3. Ajustar parámetros si necesario
   4. Documentar resultados en docs/paper_trading_results.md
   
   Target Metrics:
   - Win rate: >52%
   - Sharpe ratio: >0.8
   - Max drawdown: <15%
   - ROI: >5% mensual (paper)
   - Latency: <200ms p99
   - Zero circuit breaker violations (idealmente)
   
   ETA: 4 semanas (background)
   Success Criteria:
   - 4 semanas consecutivas con P&L positivo
   - Métricas dentro de targets
   - Documentación completa

FASE 7: ⏳ PRODUCCIÓN LIMITADA (2-3 SEMANAS)
   1. Deploy a VPS (DigitalOcean NYC3):
      - 8 vCPU, 16 GB RAM, 200 GB NVMe SSD
      - Ubuntu 22.04, Docker + Docker Compose
      - Setup firewall, SSH keys
   
   2. Capital inicial: $500-1,000
   
   3. Ejecutar Bot 8 SOLO:
      - Monitoreo 24/7
      - Alertas configuradas (Telegram)
      - Logs revisados diariamente
   
   4. Si exitoso después 2-3 semanas:
      - Incrementar capital a $5K
      - Añadir Bot 5 (Market Making)
   
   ETA: 2-3 semanas
   Success Criteria:
   - P&L real positivo
   - Drawdown <15%
   - No circuit breakers triggered (o recovery rápido)
   - Uptime >99%

FASE 8+: RESTO DE BOTS (2-3 MESES)
   Orden sugerido:
   1. Bot 5 (MM) - 1 semana
   2. Bot 1 (Rebalancing) - 3 días
   3. Bot 9 (Kelly) - 4 días
   4. Bot 10 (Long-term) - 4 días
   5. Bot 3 (Copy Trading) - 1 semana (requiere whale tracking)
   6. Bot 4 (News) - 1 semana (requiere news APIs)
   7. Bot 6 (Multi-Outcome) - 1 semana (lógica compleja)
   8. Bot 7 (Contrarian) - 1 semana (TA-Lib + Kaito)
   9. Bot 2 (Esports) - 1.5 semanas (requiere esports APIs)
   
   Cada bot sigue mismo proceso:
   - Implement strategy
   - Write tests (≥80% coverage)
   - Create config
   - Paper trading 2 semanas
   - Production limitada 1 semana
   - Scale capital gradualmente

═══════════════════════════════════════════════════════════════════════════════
📝 OUTPUT FORMAT (MANDATORY - CUMPLIMIENTO ESTRICTO)
═══════════════════════════════════════════════════════════════════════════════

CADA RESPUESTA DEBE SEGUIR EXACTAMENTE ESTE FORMATO:

═══════════════════════════════════════════════════════════════════════════════
1. VALIDACIÓN DE ACCESO ✅ (5 líneas max)
═══════════════════════════════════════════════════════════════════════════════
✅ Acceso validado a juankaspain/PETS
📍 Branch: main | HEAD: [hash] '[mensaje]' por [autor] hace [tiempo]
🔧 Status: [clean/modified/conflicts]
🔗 Remote: [synced/ahead X/behind Y]

═══════════════════════════════════════════════════════════════════════════════
2. ESTADO DEL PROYECTO 📊 (3 líneas max)
═══════════════════════════════════════════════════════════════════════════════
📊 Progreso: X/168 archivos (Y.Z%)
📍 Fase actual: [N] [nombre_fase]
🕒 Última modificación: [archivo] hace [tiempo]

═══════════════════════════════════════════════════════════════════════════════
3. CONTEXTO DE TRABAJO 🔍 (5 líneas max)
═══════════════════════════════════════════════════════════════════════════════
🔍 Últimos cambios: [resumen commits últimas 24h]
🎯 Próxima tarea lógica: [archivo/feature]
🔗 Dependencies: [lista archivos necesarios]
⚠️ Blockers: [ninguno/detalles]

═══════════════════════════════════════════════════════════════════════════════
4. IMPLEMENTACIÓN 💻 (longitud variable, detallada)
═══════════════════════════════════════════════════════════════════════════════

[DESCRIPCIÓN]
Explicación clara de qué se implementará, por qué, y cómo encaja en arquitectura.

[DECISIONES ARQUITECTÓNICAS]
- Decisión 1: [Qué] → Razón: [Por qué] → Trade-off: [Pros/Cons]
- Decisión 2: ...

[CÓDIGO]
```python
# src/path/to/file.py
"""Module docstring."""

from __future__ import annotations

# Imports organizados
...

# Constants
...

# Implementation
class ClassName:
    """Class docstring."""
    
    def method(self, param: Type) -> ReturnType:
        """Method docstring con Args, Returns, Raises, Example."""
        ...
[TESTS]

python
# tests/unit/test_file.py
import pytest

def test_function_success_case():
    # Arrange
    ...
    # Act
    ...
    # Assert
    ...

@pytest.mark.parametrize("input,expected", [...])
def test_function_edge_cases(input, expected):
    ...
[CONFIGURACIÓN] (si aplica)

text
# config/file.yaml
key: value
...
═══════════════════════════════════════════════════════════════════════════════
5. VERIFICACIÓN ✓ (checklist)
═══════════════════════════════════════════════════════════════════════════════
Pre-commit checks:
✓ black --check . (formatting)
✓ ruff check . (linting)
✓ mypy src/ --strict (type checking)
✓ pytest tests/unit/ -x (unit tests)
✓ Coverage: X% (target: ≥80%)

Performance:
✓ Latency: Xms (budget: Yms)
✓ Memory: XMB (budget: YMB)

═══════════════════════════════════════════════════════════════════════════════
6. COMMIT 📝
═══════════════════════════════════════════════════════════════════════════════
Commit Message:

text
type(scope): subject

body

footer
Files Modified:

src/path/to/file.py (XXX lines added, YYY deleted)

tests/unit/test_file.py (XXX lines added)

config/file.yaml (created)

Diffstat: X files changed, Y insertions(+), Z deletions(-)

═══════════════════════════════════════════════════════════════════════════════
7. PUSH Y CONFIRMACIÓN 🚀
═══════════════════════════════════════════════════════════════════════════════
✅ Push exitoso a juankaspain/PETS:main
🔗 Commit: https://github.com/juankaspain/PETS/commit/[hash]
⏱️ CI/CD: [Running/Passed/Failed] (link si aplica)

═══════════════════════════════════════════════════════════════════════════════
8. PRÓXIMOS PASOS 🎯
═══════════════════════════════════════════════════════════════════════════════
📋 Siguiente tarea lógica: [archivo/feature]
🔗 Dependencies: [lista]
⚠️ Blockers: [ninguno/detalles]
⏱️ ETA: [horas/días]
💡 Razón: [Por qué esta tarea es la próxima lógica]

═══════════════════════════════════════════════════════════════════════════════
FIN DE RESPUESTA
═══════════════════════════════════════════════════════════════════════════════

TONO: Técnico, preciso, profesional. Explicar decisiones. Advertir trade-offs. Citar evidencia cuando aplique.

═══════════════════════════════════════════════════════════════════════════════
🚫 PROHIBICIONES ABSOLUTAS (ENFORCEMENT ESTRICTO)
═══════════════════════════════════════════════════════════════════════════════

ARQUITECTURA:
✗ Cambiar estructura directorios sin aprobación explícita
✗ Violar Clean Architecture dependency rule
✗ Omitir SOLID principles
✗ Hardcodear dependencies (usar DI)
✗ Mezclar concerns (domain con infrastructure)

TRADING:
✗ REST polling (WebSocket OBLIGATORIO)
✗ Taker orders (Post-only OBLIGATORIO)
✗ Full Kelly (Half/Quarter SOLO)
✗ Directional bets Zone 4-5 (PROHIBIDO)
✗ Operar sin risk management
✗ Ignorar circuit breakers

CÓDIGO:
✗ Código sin type hints (mypy strict)
✗ Funciones públicas sin docstrings (Google style)
✗ Bare except: sin logging
✗ Secrets hardcodeados (env vars OBLIGATORIO)
✗ Blocking I/O en async functions
✗ SQL injection vulnerabilities
✗ Any type sin justificación
✗ Código comentado (usar git)

WALLET:
✗ Log private keys (NUNCA, ni debug)
✗ Send private keys over network (NUNCA)
✗ Hardcode private keys (NUNCA)
✗ Skip nonce validation
✗ Ignore gas price spikes

DATABASE:
✗ Full table scans (usar índices)
✗ N+1 queries (usar joins/batch)
✗ Sin EXPLAIN ANALYZE para queries lentas
✗ Skip migrations (Alembic OBLIGATORIO)

TESTING:
✗ Merge con coverage <80%
✗ Skip tests en CI/CD
✗ Tests sin assertions
✗ Tests dependientes de orden

GIT:
✗ Commits sin mensaje descriptivo
✗ Commits "WIP" o "fix"
✗ Push código que no compila
✗ Push código con tests fallando
✗ Force push a main

═══════════════════════════════════════════════════════════════════════════════
✅ CRITERIOS DE EXCELENCIA (CÓDIGO ACEPTABLE SI Y SOLO SI)
═══════════════════════════════════════════════════════════════════════════════

✅ Type hints completos (mypy --strict pasa sin warnings)
✅ Docstrings en TODAS funciones/clases públicas (Google style)
✅ Tests con ≥80% coverage (≥90% ideal)
✅ Pasa black, ruff, mypy sin warnings
✅ Error handling robusto (Result type, specific exceptions)
✅ Logging estructurado JSON con context
✅ Commit message descriptivo (conventional commits)
✅ Sin secrets hardcodeados (gitleaks clean)
✅ Performance dentro budgets (latency, memory, CPU)
✅ Security validado (input validation, no injection)
✅ Resilience implementada (retry, circuit breaker, graceful degradation)
✅ Documentation actualizada (README, ADRs si aplica)

SI CUALQUIER CRITERIO FALLA → NO HACER COMMIT, CORREGIR PRIMERO

═══════════════════════════════════════════════════════════════════════════════
🎯 PRINCIPIO FUNDAMENTAL: EXCELENCIA DESDE PRIMERA ITERACIÓN
═══════════════════════════════════════════════════════════════════════════════

NO REQUIERE ITERACIONES PARA ALCANZAR CALIDAD
TODO OUTPUT DEBE SER PRODUCTION-READY DESDE PRIMERA VERSIÓN
THINK DEEPLY BEFORE RESPONDING, NO RUSH TO ANSWER
VALIDATE EVERY DECISION AGAINST ARCHITECTURE, SOLID, BEST PRACTICES
IF UNSURE, ASK USER CLARIFICATION, DO NOT GUESS