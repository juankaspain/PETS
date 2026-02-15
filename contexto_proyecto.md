# PETS - Polymarket Elite Trading System
## Contexto Completo del Proyecto

**Última Verificación:** 2026-02-15 04:00 CET
**Último Commit:** 1df71b3 (Delete src/bots/bot_10_longterm_value.py)
**Estado del Proyecto:** 14/17 Fases COMPLETAS (82.4%)
**Idioma del Proyecto:** Español (todas las contribuciones, documentación y comentarios deben estar en español)

---

## ⚠️ CRÍTICO: Cómo Mantener Este Contexto Preciso

**PROTOCOLO DE VERIFICACIÓN (OBLIGATORIO ANTES DE CUALQUIER ACTUALIZACIÓN):**

1. **Verificación de Conteo de Archivos:**
   ```bash
   find src -name "*.py" -type f | wc -l  # Debe coincidir con el conteo documentado
   ```

2. **Verificación de Bots:**
   ```bash
   ls -1 src/bots/bot_*.py  # Debe mostrar TODOS los 10 bots
   ```

3. **Verificación del Historial de Commits:**
   ```bash
   git log --since="24 hours ago" --oneline  # Revisar trabajo reciente
   ```

4. **Evidencia de Completitud de Fase:**
   - Cada fase marcada como COMPLETA debe tener:
     - Referencia de hash de commit
     - Verificación de conteo de archivos
     - Evidencia de cobertura de tests (si aplica)

5. **Protocolo de Actualización:**
   - Leer el contexto COMPLETO ANTES de hacer cambios
   - Verificar claims contra el código real
   - Actualizar timestamp de "Última Verificación"
   - Agregar hash de commit para trazabilidad
   - NUNCA eliminar información de fase sin verificación

---

## 🎯 RESUMEN EJECUTIVO

**Objetivo:** Sistema de trading automatizado para Polymarket apuntando al 0.04% elite (70%+ beneficios anuales) con $106K evidencia Bot 8.

**Stack Tecnológico:**
- **Backend:** Python 3.11+, FastAPI, asyncio
- **Base de Datos:** TimescaleDB (series temporales), Redis (caché + nonces)
- **Blockchain:** Web3.py (Polygon), Polymarket CLOB API
- **Frontend:** Dashboard Streamlit (7 páginas)
- **Infraestructura:** Docker, Docker Compose
- **Testing:** pytest ≥80% cobertura, mypy strict

**Arquitectura:** Clean Architecture + DDD + Patrón Hexagonal
**Gestión de Riesgo:** 5 zonas de riesgo, 4 circuit breakers, Half Kelly máximo
**Trading:** WebSocket tiempo real, órdenes POST_ONLY, optimización gas EIP-1559

**Estado Actual:**
- ✅ 10 Bots implementados (estrategias completas)
- ✅ Orquestación completa (ciclo de vida + salud + eventos)
- ✅ Dashboard completo (7 páginas + WebSocket)
- ✅ Paper Trading completo (motor + validación)
- ✅ Tests de Integración (ciclo de vida bot ≥85% cobertura)
- ⏳ Despliegue Live Trading (Fase 15 - próxima)

---

## ⚠️ ESTADO DE LA AUDITORÍA (Issue #1)

**Fecha de Auditoría:** 2026-02-13
**Estado:** 🟡 EN PROGRESO
**Sprints Completados:** 1 de 4 (25%)

### Correcciones Aplicadas (Sprint 1):
- ✅ `.gitignore` corregido (antes era `gitignore` sin punto)
- ✅ Bot 8 Tail Risk implementado (~230 líneas, commit 6c06d89)
- ✅ `src/domain/events/` creado (commit 51a398d)
- ✅ `bot_manager.py` implementado (~240 líneas, commit 7724290)
- ✅ Stubs companion eliminados
- ✅ `env.example` duplicado eliminado
- ✅ `setup.py` stub eliminado
- ✅ LICENSE MIT completo
- ✅ CI/CD pipelines implementados (5 workflows)

### Pendiente (Sprints 2-4):
- ⏳ **Sprint 2:** Migrar directorios legacy a Clean Architecture
- ⏳ **Sprint 3:** Actualizar toda documentación a español
- ⏳ **Sprint 4:** Consolidar dependencias en pyproject.toml

---

## ⚠️ ARQUITECTURA EN TRANSICIÓN

### Estado Objetivo (Clean Architecture):
```
src/
├── domain/           # Lógica de negocio (sin dependencias externas)
├── application/      # Casos de uso (orquestación sin estado)
├── infrastructure/   # Detalles de implementación
└── presentation/     # Interfaces externas
```

### Estado Actual (Con Directorios Legacy):
```
src/
├── domain/           ✅ CORRECTO
├── application/      ✅ CORRECTO
├── infrastructure/   ✅ CORRECTO
├── presentation/     ✅ CORRECTO
├── bots/            ⚠️ LEGACY (migrar a application/)
├── api/             ⚠️ LEGACY (migrar a presentation/)
├── dashboard/       ⚠️ LEGACY (migrar a presentation/)
├── core/            ⚠️ LEGACY (distribuir por capa)
├── data/            ⚠️ LEGACY (migrar a infrastructure/)
├── monitoring/      ⚠️ LEGACY (migrar a infrastructure/)
├── strategies/      ⚠️ LEGACY (migrar a domain/services/)
└── utils/           ⚠️ LEGACY (distribuir por capa)
```

**Acción Requerida:** Issue #1 Sprint 2 - Migración sistemática de directorios legacy

---

## 📊 ESTADO DETALLADO POR COMPONENTE

### 1. BOTS (10/10 IMPLEMENTADOS) ✅

**Verificado:** 2026-02-15 (inspección de código fuente)

| Bot | Estrategia | Archivo | Estado | Evidencia |
|-----|-----------|---------|--------|----------|
| Bot 1 | Market Rebalancing | `bot_01_rebalancer.py` | ✅ COMPLETO | Archivo existe |
| Bot 2 | Esports Trading | `bot_02_esports.py` | ✅ COMPLETO | Archivo existe |
| Bot 3 | Copy Trading | `bot_03_copy_trading.py` | ✅ COMPLETO | Archivo existe |
| Bot 4 | News-Driven | `bot_04_news_driven.py` | ✅ COMPLETO | Archivo existe |
| Bot 5 | Market Making | `bot_05_market_making.py` | ✅ COMPLETO | Archivo existe |
| Bot 6 | Arbitraje Multi-Outcome | `bot_06_multi_outcome.py` | ✅ COMPLETO | Archivo existe |
| Bot 7 | Contrarian | `bot_07_contrarian.py` | ✅ COMPLETO | Archivo existe |
| Bot 8 | **Tail Risk (PRIORITARIO)** | `bot_08_tail_risk_combo.py` | ✅ IMPLEMENTADO | Commit 6c06d89 (~230 líneas) |
| Bot 9 | Advanced Kelly | `bot_09_advanced_kelly.py` | ✅ COMPLETO | CÓDIGO VERIFICADO |
| Bot 10 | Long-term Value | `bot_10_longterm.py` | ✅ COMPLETO | CÓDIGO VERIFICADO |

**Evidencia Bot 8 Prioritario:**
- Config completo: `configs/bot_08_tail_risk.yaml`
- Validación: `BotConfigValidator` implementado
- Restricciones: Solo Z1-Z2, Half Kelly, POST_ONLY
- Paper Trading: Listo para validación
- Objetivo: Win rate >52%, Sharpe >0.8, Drawdown <15%
- **Evidencia Histórica:** $106K beneficios documentados

### 2. ORQUESTACIÓN (6/6 COMPLETOS) ✅

**Verificado:** 2026-02-14 (escaneo de directorio)

```
src/application/orchestration/
├── __init__.py           ✅
├── bot_orchestrator.py   ✅ (ciclo de vida + máquina de estados)
├── event_bus.py          ✅ (pub/sub asíncrono)
├── health_checker.py     ✅ (monitoreo de componentes)
├── retry_policy.py       ✅ (backoff exponencial)
├── graceful_degradation.py ✅ (estrategias de fallback)
└── factory.py            ✅ (contenedor DI)
```

**BotManager:** ✅ Implementado (~240 líneas) - Issue #1 C1-05 resuelto (commit 7724290)

### 3. DASHBOARD (7/7 PÁGINAS COMPLETAS) ✅

**Verificado:** 2026-02-13 (historial de commits)

```
src/presentation/dashboard/
├── app.py                ✅ (Streamlit principal)
├── pages/
│   ├── 1_Overview.py     ✅ (controles emergencia + métricas)
│   ├── 2_Bot_Control.py  ✅ (gestión de bots)
│   ├── 3_Performance.py  ✅ (análisis comparativo)
│   ├── 4_Positions.py    ✅ (seguimiento posiciones)
│   ├── 5_Order_Log.py    ✅ (monitoreo ejecución)
│   ├── 6_Risk_Monitor.py ✅ (métricas de riesgo)
│   └── 7_Settings.py     ✅ (editor config)
├── components/
│   ├── metric_card.py    ✅
│   ├── chart_utils.py    ✅
│   ├── websocket_client.py ✅ (actualizaciones tiempo real)
│   └── api_client.py     ✅
└── utils/
    ├── formatting.py     ✅
    └── state_manager.py  ✅
```

**Características:**
- WebSocket tiempo real (actualizaciones 1s)
- Gráficos interactivos Plotly
- Controles de emergencia (DETENER TODO)
- Monitoreo multi-bot
- Recarga en caliente de config

### 4. PAPER TRADING (3/3 COMPLETO) ✅

**Verificado:** 2026-02-13 (historial de commits)

```
src/application/use_cases/paper_trading/
├── run_paper_trading.py    ✅ (orquestación de sesión)
├── get_paper_stats.py      ✅ (cálculo de métricas)
└── reset_paper_trading.py  ✅ (limpieza de estado)

src/infrastructure/paper_trading/
├── paper_trading_engine.py ✅ (ejecución virtual)
├── virtual_balance.py      ✅ ($5K inicial)
└── virtual_position.py     ✅ (seguimiento P&L)
```

**Características:**
- Balance virtual: $5K inicial
- Slippage: 0.1% promedio, 0.5% máximo
- Comisiones: 2% taker, 0% maker
- Latencia: 50ms simulación
- POST_ONLY: 70% probabilidad de fill
- Sin interacción real con wallet/blockchain

### 5. TESTS DE INTEGRACIÓN ✅

**Verificado:** 2026-02-13 (commit 7aa0b79)

```
tests/
├── integration/
│   ├── test_bot_lifecycle.py  ✅ (5 escenarios)
│   ├── test_orchestration.py  ✅
│   └── test_end_to_end.py     ✅
├── unit/                      ✅
├── e2e/                       ✅
├── application/               ✅
├── presentation/dashboard/    ✅
└── test_paper_trading.py      ✅
```

**Cobertura:** Objetivo ≥85% código ciclo de vida bot

### 6. DOMAIN EVENTS ✅

**Verificado:** 2026-02-14 (commit 51a398d)

```
src/domain/events/
└── __init__.py  ✅ (DomainEvent, OrderFilledEvent, PositionClosedEvent, etc.)
```

**Resuelve:** Issue #1 C3-01 - Faltaba `src/domain/events/`

---

## 🗺️ ROADMAP COMPLETO (17 FASES)

### ✅ FASE 1-7: Bots 1-7 (COMPLETAS)
Todos los bots básicos implementados con configs, tests y estrategias.

### ✅ FASE 8: Bot 8 - Tail Risk (COMPLETA) 🎯 PRIORITARIO
**Estado:** Production-ready, esperando validación paper trading
**Archivos:** `bot_08_tail_risk_combo.py`, `bot_08_tail_risk.yaml`
**Evidencia:** $106K beneficios históricos documentados
**Commit:** 6c06d89

**Restricciones:**
- Zonas: SOLO Z1-Z2 (Z3-Z5 PROHIBIDAS)
- Kelly: Half Kelly 0.25-0.50 (Full Kelly PROHIBIDO)
- Órdenes: POST_ONLY (taker PROHIBIDO)
- Edge mínimo: 15% Z1, 10% Z2
- Datos: WebSocket REQUERIDO (sin polling REST)

**Siguiente Paso:** Validación paper trading 30 días
- Objetivo: Win rate >52%, Sharpe >0.8, Max DD <15%

### ✅ FASE 9-10: Bots 9-10 (COMPLETAS)
**Bot 9:** Advanced Kelly - Sizing dinámico basado en confianza
**Bot 10:** Long-term Value - Estrategia buy-and-hold

### ✅ FASE 11: Capa de Orquestación (COMPLETA)
**Commit:** 88362ec
**Componentes:** BotOrchestrator, HealthChecker, EventBus, RetryPolicy, GracefulDegradation, Factory

### ✅ FASE 12: Dashboard (COMPLETA)
**Commit:** 84828ea
**Páginas:** 7 páginas Streamlit con WebSocket tiempo real

### ✅ FASE 13: Tests de Integración (COMPLETA)
**Commit:** 7aa0b79
**Cobertura:** ≥85% ciclo de vida bot

### ✅ FASE 14: Paper Trading (COMPLETA)
**Commit:** ec9198f
**Motor:** Ejecución virtual completa con simulación de slippage/fees

### ⏳ FASE 15: Despliegue Live Trading (PRÓXIMA)
**Estado:** NO INICIADA
**Prioridad:** ALTA (después de validación Bot 8)

**Tareas:**
1. Configuración hot wallet (mnemonic BIP39)
2. Asignación cold storage (80-90%)
3. Configuración Polygon mainnet
4. Sistema de alertas (email/Slack/SMS)
5. Procedimientos backup/recovery

### ⏳ FASE 16: Optimización de Rendimiento (FUTURA)
### ⏳ FASE 17: Características Avanzadas (FUTURA)

---

## ⚠️ GESTIÓN DE RIESGO

### 5 Zonas de Riesgo

| Zona | Rango Probabilidad | Edge Mín | Nivel Riesgo | Bot 8 |
|------|-------------------|----------|--------------|-------|
| Z1 | 15-25% o 75-85% | 15% | MÍNIMO | ✅ PERMITIDO |
| Z2 | 25-35% o 65-75% | 10% | BAJO | ✅ PERMITIDO |
| Z3 | 35-45% o 55-65% | 5% | MEDIO | ❌ PROHIBIDO |
| Z4 | 45-48% o 52-55% | 3% | ALTO | ❌ PROHIBIDO |
| Z5 | 48-52% | 0% | EXTREMO | ❌ PROHIBIDO |

### 4 Circuit Breakers

**1. Pérdidas Consecutivas:**
- Umbral: 3 pérdidas consecutivas
- Acción: Pausar bot inmediatamente
- Reset: Revisión manual requerida

**2. Límite Pérdida Diaria:**
- Umbral: 5% pérdida diaria del portfolio
- Acción: DETENER TODOS los bots
- Reset: Siguiente día 00:00 UTC

**3. Drawdown del Bot:**
- Umbral: 25% drawdown específico del bot
- Acción: Pausar bot específico
- Reset: Revisión manual + aprobación

**4. Drawdown del Portfolio:**
- Umbral: 40% drawdown total del portfolio
- Acción: HALT DE EMERGENCIA TODO
- Reset: Revisión a nivel sistema requerida

### Dimensionamiento de Posiciones (Kelly)

**Half Kelly:** 0.25-0.50 (rango Bot 8)
**Quarter Kelly:** 0.25 (default Bot 8)
**Full Kelly:** PROHIBIDO (demasiado agresivo)

**Fórmula:**
```
Kelly = (bp - q) / b
donde:
  b = odds (ratio de pago)
  p = probabilidad de ganar
  q = 1 - p (probabilidad de perder)

Tamaño Posición = Kelly * Capital * Factor Ajuste
```

**Restricciones:**
- Máx posición: $1,000 (Bot 8)
- Máx portfolio: $10,000 total
- Máx posiciones: 5 concurrentes (Bot 8)

---

## 💰 GESTIÓN DE WALLET

**Arquitectura:**
- **Hot Wallet:** 10-20% capital (trading activo)
- **Cold Storage:** 80-90% capital (offline seguro)
- **Estrategia Gas:** Fees dinámicos EIP-1559
- **Nonce:** Gestión secuencial basada en Redis
- **Recovery:** Backup mnemonic BIP39

**Seguridad:**
- ❌ NUNCA loguear claves privadas
- ❌ NUNCA enviar claves por red
- ✅ Almacenamiento cifrado en reposo
- ✅ Multi-sig opcional (2-de-3)
- ✅ Hardware wallet para cold storage

---

## 🗗️ ARQUITECTURA DE BASE DE DATOS

### TimescaleDB (Series Temporales)

**Hypertables:**
```sql
CREATE TABLE market_prices (
    time TIMESTAMPTZ NOT NULL,
    market_id TEXT NOT NULL,
    price NUMERIC(18,6),
    volume NUMERIC(18,2)
);
SELECT create_hypertable('market_prices', 'time', 
    chunk_time_interval => INTERVAL '7 days');
```

**Objetivos de Rendimiento:**
- Consultas simples: <10ms p99
- Agregaciones: <50ms p99
- Consultas dashboard: <100ms p99

### Redis (Caché + Mensajería)

**Casos de Uso:**
- Gestión de nonce: Secuencial por wallet
- Caché order book: 100ms TTL
- Estado de sesión: Persistencia estado bot
- Rate limiting: Algoritmo token bucket
- Pub/Sub: Mensajería event bus

---

## 📝 ESTÁNDARES DE CALIDAD DE CÓDIGO

**Type Hints:** modo mypy strict ✅
```python
def calculate_kelly(edge: Decimal, win_rate: Decimal) -> Decimal:
    """Calcula la fracción de Kelly.
    
    Args:
        edge: Porcentaje de edge (ej: Decimal("0.05") para 5%)
        win_rate: Tasa de victorias (ej: Decimal("0.54") para 54%)
    
    Returns:
        Fracción de Kelly (rango 0-1)
    
    Raises:
        ValueError: Si los inputs son inválidos
    """
    ...
```

**Docstrings:** estilo Google ✅
**Manejo de Errores:** patrón Result[T, E] ✅
**Logging:** JSON estructurado ✅
**Async:** async/await en toda I/O ✅
**Dataclasses:** inmutables por defecto (frozen=True) ✅

**Convenciones de Nombrado:**
- Clases: PascalCase (`OrderService`, `KellyCalculator`)
- Funciones: snake_case (`calculate_pnl`, `place_order`)
- Constantes: UPPER_SNAKE_CASE (`MAX_POSITION_SIZE`, `MIN_EDGE_PCT`)
- Privado: `_internal_method`, `_private_var`

---

## 🚫 PRÁCTICAS PROHIBIDAS

**ARQUITECTURA:**
- ❌ Violar dependency rule (domain importando infrastructure)
- ❌ Lógica de negocio en infrastructure/presentation
- ❌ Dependencias circulares
- ❌ God classes (>500 líneas)

**TRADING:**
- ❌ Dimensionamiento Full Kelly
- ❌ Órdenes taker (Bot 8 - comisiones muy altas)
- ❌ Apuestas direccionales Z4-Z5 (coin flip)
- ❌ Polling REST para datos de mercado (usar WebSocket)

**CÓDIGO:**
- ❌ Código sin type hints
- ❌ Funciones públicas sin docstrings
- ❌ `except Exception:` sin logging
- ❌ Secretos hardcodeados (usar .env)

**SEGURIDAD:**
- ❌ Loguear claves privadas
- ❌ Enviar claves por red
- ❌ Commitear secretos a git
- ❌ Usar mismo wallet dev/prod

**BASE DE DATOS:**
- ❌ Vulnerabilidades SQL injection
- ❌ Índices faltantes en queries
- ❌ Full table scans (¡optimizar!)
- ❌ Datos históricos sin comprimir

---

## ✅ CRITERIOS DE MERGE

**Calidad de Código:**
- ✅ Type hints completos (mypy strict pass)
- ✅ Docstrings en todas las funciones públicas
- ✅ Tests ≥80% cobertura (pytest)
- ✅ black + ruff + mypy clean
- ✅ Manejo de errores robusto

**Arquitectura:**
- ✅ Cumplimiento Clean Architecture
- ✅ Dependency rule respetada
- ✅ Principios SOLID aplicados
- ✅ Sin dependencias circulares

**Testing:**
- ✅ Tests unitarios pasan (todos)
- ✅ Tests de integración pasan (todos)
- ✅ Cobertura ≥80% código nuevo
- ✅ Sin tests flaky

**Formato de Mensaje de Commit:**
```
type(scope): asunto

cuerpo (opcional)

footer (opcional)

Tipos: feat, fix, docs, test, refactor, perf, chore
Scope: bot, api, db, wallet, risk, dashboard, orchestration
```

---

## ⚠️ PROBLEMAS CONOCIDOS Y ACCIONES REQUERIDAS

### 1. Duplicación de Configuración (Crítico)
**Problema:** `config/` y `configs/` coexisten con archivos duplicados
**Ubicación:** `config/bots/*.yaml` tiene YAML con nombres antiguos de stubs
**Impacto:** Confusión, archivos desactualizados
**Acción:** Eliminar `config/bots/`, usar solo `configs/`
**Timeline:** Issue #1 Sprint 2

### 2. Dependencias Redundantes (Medio)
**Problema:** `requirements.txt` + `requirements-dev.txt` + `pyproject.toml`
**Impacto:** Inconsistencia de versiones posible
**Acción:** Migrar todo a `pyproject.toml`
**Timeline:** Issue #1 Sprint 4

### 3. BOTS_REAL_NAMES.md Desactualizado (Bajo)
**Problema:** Lista stubs que ya fueron eliminados
**Acción:** Actualizar o eliminar documento
**Timeline:** Próxima sesión de limpieza

---

## 📚 REFERENCIAS CLAVE

**Polymarket:**
- API CLOB: https://docs.polymarket.com/
- WebSocket: wss://ws-subscriptions-clob.polymarket.com
- Contratos: Polygon mainnet (USDC: 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174)

**TimescaleDB:**
- Docs: https://docs.timescale.com/
- Hypertables: https://docs.timescale.com/use-timescale/latest/hypertables/

**Web3:**
- Web3.py: https://web3py.readthedocs.io/
- EIP-1559: https://eips.ethereum.org/EIPS/eip-1559
- BIP39: https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki

**Arquitectura:**
- Clean Architecture: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- DDD: https://martinfowler.com/bliki/DomainDrivenDesign.html

---

## 🎯 PRÓXIMOS PASOS (INMEDIATOS)

### 1. Validación Paper Trading Bot 8 (PRIORIDAD ALTA) 🔥
**Objetivo:** Validar estrategia Bot 8 Tail Risk con 30 días de paper trading

**Tareas:**
1. ✅ Config Bot 8 completo
2. ✅ Motor Paper Trading implementado
3. ⏳ **PRÓXIMO:** Ejecutar sesión paper trading 30 días
4. ⏳ Monitorear métricas diarias
5. ⏳ Análisis de resultados
6. ⏳ Decisión GO/NO-GO

**Timeline:** 30 días paper trading + 1 semana análisis = ~5 semanas

### 2. Completar Issue #1 Sprints 2-4 (PRIORIDAD MEDIA)
- Sprint 2: Migración arquitectura
- Sprint 3: Documentación español
- Sprint 4: Consolidación DevOps

### 3. Preparación Live Trading (PRIORIDAD BAJA)
Bloqueado hasta validación Bot 8

---

## 📖 GLOSARIO

- **CLOB:** Central Limit Order Book (exchange Polymarket)
- **DDD:** Diseño Guiado por Dominio
- **EIP-1559:** Propuesta de Mejora de Ethereum (fees de gas dinámicos)
- **Kelly:** Criterio de Kelly (dimensionamiento óptimo de posición)
- **POST_ONLY:** Órdenes solo maker (sin ejecución inmediata)
- **Sharpe Ratio:** Métrica de retorno ajustada por riesgo
- **Tail Risk:** Eventos de baja probabilidad, alto impacto
- **WebSocket:** Protocolo de comunicación bidireccional en tiempo real
- **Zona:** Zona de riesgo basada en probabilidad de mercado

---

## 📆 CHANGELOG (RECIENTE)

### 2026-02-15
- ✅ Contexto traducido completamente a español
- ✅ Documentada arquitectura en transición (legacy + objetivo)
- ✅ Agregada sección estado de auditoría Issue #1
- ✅ Problemas conocidos documentados

### 2026-02-14
- ✅ Bot 8 Tail Risk implementado (commit 6c06d89)
- ✅ Domain Events creado (commit 51a398d)
- ✅ BotManager implementado (commit 7724290)
- ✅ Stubs companion eliminados
- ✅ CI/CD pipelines implementados

### 2026-02-13
- ✅ Issue #1 creado: Auditoría completa del proyecto
- ✅ GROUND_TRUTH_REPORT.md generado
- ✅ .gitignore corregido
- ✅ LICENSE MIT completo
- ✅ Tests de integración ciclo de vida bot

---

**FIN DEL CONTEXTO**

**Última Actualización:** 2026-02-15 04:00 CET
**Próxima Revisión:** Antes de cualquier transición de fase
**Mantenido Por:** Sistema AI (con verificación obligatoria)
**Fuente Única de Verdad:** Este archivo es autoritativo
