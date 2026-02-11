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
- `Position`: position_id, bot_id, order_id, market_id, side, size, entry_price, current_price, pnl, zone, opened_at
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

#### Dashboard (`src/presentation/dashboard/`)

**Streamlit multi-page app**, **7 páginas**:

**1. 🏠 Overview**: Emergency controls, metrics cards (1s updates), P&L chart, portfolio composition, zone heatmap

**2. 🤖 Bot Control**: Bot status grid, detail panel (metrics, charts, config editor, logs, actions), state diagram

**3. 📈 Performance**: Comparative table, ROI chart, risk-adjusted scatter, drawdown analysis, trade distributions

**4. 💰 Positions**: Active table (1s updates), position modal, closed history, position heatmap

**5. 📜 Order Log**: Execution table (2s updates), filters, performance metrics, latency distribution, rejection analysis

**6. ⚠️ Risk Monitor**: Zone exposure, circuit breaker status, drawdown gauges, consecutive loss tracker, risk alerts feed

**7. ⚙️ Settings**: 5 tabs (Global config, Bot-specific, Notifications, Database, System health)

---

### Bots Layer (`src/bots/`)

**BaseBotStrategy** (ABC):
- Abstract: initialize, execute_cycle, stop_gracefully, get_state, get_metrics
- Implemented: start, pause, resume, stop, emergency_halt
- State machine: IDLE → STARTING → ACTIVE ⇄ PAUSED → STOPPING → STOPPED/ERROR

**Concrete Bots**: bot_01_*.py ... bot_10_*.py (cada uno con config YAML)

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

### Fase 3: ⏳ Core Services (ACTUAL - 1 SEMANA)
models.py, redis_client.py, timescaledb.py, event_bus.py, wallet_manager.py, gas_manager.py, websocket_gateway.py, market_data_processor.py, risk_manager.py, order_execution_engine.py
**ETA**: 40h

### Fase 4: ⏳ Bot 8 Prototype (1 SEMANA)
base_bot.py, tail_risk strategies, market_making strategies, bot_08_tail_risk_combo.py, tests ≥85%, config YAML
**ETA**: 40h
**Razón**: Mejor evidencia ($106K planktonXD)

### Fase 5: ⏳ Dashboard MVP (3-4 DÍAS)
app.py, WebSocket client, API client, components, 7 pages
**ETA**: 28h

### Fase 6: ⏳ Paper Trading (4 SEMANAS)
Bot 8 paper mode, win rate >52%, Sharpe >0.8, drawdown <15%
**ETA**: 4 semanas paralelo

### Fase 7: ⏳ Producción Limitada (2-3 SEMANAS)
$500-1K capital, Bot 8 solo, monitoreo 24/7, si exitoso → $5K + Bot 5

### Fase 8+: Resto Bots (2-3 MESES)
Bot 5 (MM), Bot 1 (Rebalancing), Bot 9 (Kelly), Bot 10 (Long-term), Bot 3 (Copy), Bot 4 (News), Bot 6 (Multi-Outcome), Bot 7 (Contrarian), Bot 2 (Esports)

---

## 💻 Estándares de Código

### Type Safety
```python
# mypy --strict OBLIGATORIO
def calculate_kelly(p: float, odds: float) -> Decimal:
    ...
```

### Docstrings
```python
def place_order(order: Order) -> OrderId:
    """Place order with risk validation.

    Args:
        order: Order with validated price/size

    Returns:
        OrderId if successful

    Raises:
        RiskViolationError: If violates rules
        OrderRejectedError: If Polymarket rejects

    Example:
        >>> order_id = await place_order(order)
    """
    ...
```

### Error Handling (Result Type)
```python
Result = Union[Ok[T], Err[E]]

result = divide(10, 0)
match result:
    case Ok(value): ...
    case Err(error): ...
```

### Logging (JSON)
```python
logger.info("order_placed", extra={
    "bot_id": 8, "order_id": str(order.id),
    "correlation_id": ctx.correlation_id
})
```

### Async/Await
```python
# CORRECTO: Concurrent
results = await asyncio.gather(*tasks)

# PROHIBIDO: Blocking I/O
response = requests.get(url)  # ❌
```

### Input Validation
```python
class OrderRequest(BaseModel):
    price: Decimal = Field(ge=Decimal('0.01'), le=Decimal('0.99'))

    @field_validator('price')
    def validate_zones(cls, v):
        if Decimal('0.60') <= v <= Decimal('0.98'):
            raise ValueError('Zone 4-5 directional prohibited')
        return v
```

### Naming
- Classes: `PascalCase`
- Functions: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_underscore`
- Booleans: `is_`, `has_`, `can_`

### Immutability
```python
@dataclass(frozen=True)
class Price:
    value: Decimal
    zone: int
```

---

## 🚫 Prohibiciones

### Arquitectura
❌ Cambiar estructura sin OK  
❌ Violar dependency rule  
❌ Ignorar SOLID  
❌ Hardcodear dependencies  

### Trading
❌ REST polling (WebSocket OBLIGATORIO)  
❌ Taker orders (Post-only OBLIGATORIO)  
❌ Full Kelly (Half/Quarter SOLO)  
❌ Directional Z4-Z5  

### Código
❌ Sin type hints  
❌ Sin docstrings públicas  
❌ Bare except:  
❌ Secrets hardcoded  
❌ Blocking I/O async  
❌ SQL injection  
❌ Any type  

### Wallet
❌ Log private keys (NUNCA)  
❌ Send private keys (NUNCA)  
❌ Hardcode private keys (NUNCA)  

### Database
❌ Full table scans  
❌ N+1 queries  
❌ Skip EXPLAIN ANALYZE  

### Testing
❌ Merge <80% coverage  
❌ Skip tests CI/CD  

### Git
❌ Commits "WIP"/"fix"  
❌ Push broken code  

---

## ✅ Criterios Excelencia

**Código aceptable SI Y SOLO SI**:

✅ Type hints completos (mypy strict)  
✅ Docstrings Google style  
✅ Tests ≥80% coverage  
✅ black, ruff, mypy clean  
✅ Error handling robusto  
✅ JSON logging  
✅ Conventional commits  
✅ gitleaks clean  
✅ Performance budgets OK  
✅ Security validated  
✅ Resilience implemented  

---

## 📝 Commit Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: feat, fix, docs, style, refactor, perf, test, chore

**Ejemplo CORRECTO**:
```
feat(bot-08): implement tail risk scanner

- Add low_liquidity_scanner.py <$1K filter
- Integrate with market_data_processor
- 15 unit tests, 92% coverage
- Performance: <30ms scan 500 markets

Closes #42
```

**Ejemplos INCORRECTOS**: "update code", "fix bug", "WIP"

---

## 🎯 Output Format (8 Secciones)

```
1. ✅ ACCESO: Branch main HEAD [hash] clean
2. 📊 ESTADO: X/168 (Y%) Fase N
3. 🔍 CONTEXTO: Cambios + tarea + deps + blockers
4. 💻 IMPLEMENTACIÓN: Descripción + código + tests
5. ✓ VERIFICACIÓN: black ruff mypy pytest cov
6. 📝 COMMIT: type(scope): subject + body
7. 🚀 PUSH: Exitoso + link
8. 🎯 PRÓXIMOS: Siguiente + ETA + razón
```

---

## 🔄 Actualización Documento

**Actualizar cuando**:
- Nueva fase completada
- Decisión arquitectónica (+ ADR)
- Cambio roadmap
- Nuevos componentes core
- Performance benchmarks

**Commit**:
```
docs(context): update contexto_proyecto.md - [razón]
```

---

## 🎯 Principio Fundamental

**EXCELENCIA PRIMERA ITERACIÓN**

- Production-ready SIEMPRE
- Think deeply
- Validate architecture/SOLID
- Ask if unsure, don't guess

---

*Última actualización: 2026-02-12*  
*Versión: 1.1*  
*Autor: Juan [juankaspain]*
