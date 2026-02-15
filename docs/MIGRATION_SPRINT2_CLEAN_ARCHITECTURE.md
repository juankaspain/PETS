# Sprint 2: Migración a Clean Architecture

**Issue:** #1 - Auditoría Completa del Proyecto
**Fecha:** 2026-02-15
**Estado:** PENDIENTE DE EJECUCIÓN
**Prioridad:** ALTA

---

## 1. ANÁLISIS DE DUPLICADOS (Auditoría Completa)

### Hallazgo Crítico: Stubs del First Commit

El `first commit init` (4799d6e) creó una estructura de directorios con archivos placeholder
(1 línea: `# TODO: Implement ...`). Posteriormente, se implementaron los archivos reales
en la estructura Clean Architecture correcta. **Los stubs nunca fueron eliminados.**

### Tabla de Duplicados Detectados

| Directorio Legacy (STUB) | Directorio Correcto (IMPLEMENTADO) | Veredicto |
|---|---|---|
| `src/api/` (5 stubs) | `src/presentation/api/` (8 archivos reales) | ELIMINAR legacy |
| `src/dashboard/` (5 stubs) | `src/presentation/dashboard/` (8 archivos reales) | ELIMINAR legacy |
| `src/core/` (8 stubs) | `src/application/orchestration/` (7 archivos reales) | ELIMINAR legacy |
| `src/monitoring/` (6 stubs) | `src/infrastructure/monitoring/` (3 archivos reales) | ELIMINAR legacy |
| `src/data/` (7 stubs) | `src/infrastructure/persistence/` + `external_apis/` | ELIMINAR legacy |
| `src/utils/` (8 stubs) | `src/application/config/` + `src/domain/` | ELIMINAR legacy |
| `src/strategies/` (7 dirs stubs) | `src/domain/services/` | ELIMINAR legacy |
| `config/bots/` (10 templates) | `configs/` (10 YAMLs reales) | ELIMINAR legacy |
| `config/` (completo) | `configs/` + `src/application/config/` | ELIMINAR legacy |

### Caso Especial: `src/bots/` (CÓDIGO REAL)

**IMPORTANTE:** `src/bots/` NO es stub. Contiene los 10 bots implementados con código real:
- `base_bot.py` (~200+ líneas - clase base abstracta)
- `bot_01_rebalancer.py` a `bot_10_longterm.py` (código completo)
- `bot_manager.py` (~240 líneas)

**Destino:** `src/application/bots/` (ya existe con solo 2 archivos: `__init__.py` y `bot8_volatility_skew.py`)
**Acción:** MOVER archivos reales de `src/bots/` a `src/application/bots/`

### Caso Especial: `config/` vs `configs/`

| `config/bots/` (LEGACY) | `configs/` (CORRECTO) |
|---|---|
| `bot_01_market_rebalancing.yaml` (template) | `bot_01_rebalancer.yaml` (real) |
| `bot_02_esports_parsing.yaml` (template) | `bot_02_esports.yaml` (real) |
| `bot_03_copy_trading.yaml` (template) | `bot_03_copy_trading.yaml` (real) |
| `bot_04_news_scalping.yaml` (template) | `bot_04_news_driven.yaml` (real) |
| `bot_05_market_making.yaml` (template) | `bot_05_market_making.yaml` (real) |
| `bot_06_multi_outcome_arb.yaml` (template) | `bot_06_multi_outcome.yaml` (real) |
| `bot_07_contrarian_attention.yaml` (template) | `bot_07_contrarian.yaml` (real) |
| `bot_08_tail_risk_combo.yaml` (template) | `bot_08_tail_risk.yaml` (real) |
| `bot_09_kelly_value.yaml` (template) | `bot_09_advanced_kelly.yaml` (real) |
| `bot_10_longterm_value.yaml` (template) | `bot_10_longterm.yaml` (real) |

**Veredicto:** `config/bots/` son templates placeholder con `bot_id: PLACEHOLDER`.
`configs/` tiene las configuraciones reales. ELIMINAR todo `config/`.

---

## 2. ESTRUCTURA OBJETIVO (Post-Migración)

```
PETS/
├── configs/                          # Configuraciones YAML (FUENTE ÚNICA)
│   ├── bot_01_rebalancer.yaml
│   ├── ... (10 bots)
│   └── README.md
├── src/
│   ├── domain/                       # Capa de Dominio (sin dependencias externas)
│   │   ├── entities/
│   │   ├── events/
│   │   ├── protocols/
│   │   ├── services/
│   │   ├── value_objects/
│   │   └── exceptions.py
│   ├── application/                  # Capa de Aplicación (casos de uso)
│   │   ├── bots/                     # 10 bots + base_bot + bot_manager
│   │   ├── config/
│   │   ├── orchestration/
│   │   ├── orchestrator/
│   │   ├── paper_trading/
│   │   ├── production/
│   │   └── use_cases/
│   ├── infrastructure/               # Capa de Infraestructura
│   │   ├── blockchain/
│   │   ├── external/
│   │   ├── external_apis/
│   │   ├── messaging/
│   │   ├── monitoring/
│   │   ├── paper_trading/
│   │   ├── persistence/
│   │   ├── repositories/
│   │   └── wallet/
│   └── presentation/                 # Capa de Presentación
│       ├── api/
│       └── dashboard/
├── tests/
├── docs/
├── data/
├── infra/
├── notebooks/
└── scripts/
```

**Directorios ELIMINADOS tras migración:**
- `config/` (completo - usar solo `configs/`)
- `src/api/` (stubs)
- `src/core/` (stubs)
- `src/dashboard/` (stubs)
- `src/data/` (stubs)
- `src/monitoring/` (stubs)
- `src/strategies/` (stubs)
- `src/utils/` (stubs)
- `src/bots/` (movido a `src/application/bots/`)

---

## 3. COMANDOS DE MIGRACIÓN (Ejecutar en orden)

### Prerequisitos

```bash
# 1. Clonar repositorio y crear rama de migración
git clone https://github.com/juankaspain/PETS.git
cd PETS
git checkout -b refactor/sprint2-clean-architecture

# 2. Verificar estado actual antes de cambios
echo "=== VERIFICACIÓN PRE-MIGRACIÓN ==="
echo "Archivos Python en src/:"
find src -name "*.py" -type f | wc -l
echo "Bots en src/bots/:"
ls -1 src/bots/bot_*.py
echo "Bots en src/application/bots/:"
ls -1 src/application/bots/ 2>/dev/null
echo "Configs en config/bots/:"
ls -1 config/bots/
echo "Configs en configs/:"
ls -1 configs/
```

### Fase 1: Mover bots reales a Clean Architecture

```bash
# 3. Mover archivos REALES de src/bots/ a src/application/bots/
# NOTA: Mantener bot8_volatility_skew.py que ya existe en destino

# Mover base_bot.py
git mv src/bots/base_bot.py src/application/bots/base_bot.py

# Mover los 10 bots
git mv src/bots/bot_01_rebalancer.py src/application/bots/bot_01_rebalancer.py
git mv src/bots/bot_02_esports.py src/application/bots/bot_02_esports.py
git mv src/bots/bot_03_copy_trading.py src/application/bots/bot_03_copy_trading.py
git mv src/bots/bot_04_news_driven.py src/application/bots/bot_04_news_driven.py
git mv src/bots/bot_05_market_making.py src/application/bots/bot_05_market_making.py
git mv src/bots/bot_06_multi_outcome.py src/application/bots/bot_06_multi_outcome.py
git mv src/bots/bot_07_contrarian.py src/application/bots/bot_07_contrarian.py
git mv src/bots/bot_08_tail_risk_combo.py src/application/bots/bot_08_tail_risk_combo.py
git mv src/bots/bot_09_advanced_kelly.py src/application/bots/bot_09_advanced_kelly.py
git mv src/bots/bot_10_longterm.py src/application/bots/bot_10_longterm.py

# Mover bot_manager.py
git mv src/bots/bot_manager.py src/application/bots/bot_manager.py

# Mover __init__.py (sobreescribir el existente)
git mv -f src/bots/__init__.py src/application/bots/__init__.py

# Commit fase 1
git add -A
git commit -m "refactor(bots): mover 10 bots reales a application/bots/

Sprint 2 Issue #1 - Migración Clean Architecture
- Movidos base_bot.py, bot_01-10, bot_manager.py
- Destino: src/application/bots/ (capa de aplicación)
- src/bots/ eliminado (era ubicación legacy)"
```

### Fase 2: Eliminar directorios legacy (STUBS)

```bash
# 4. Eliminar TODOS los directorios legacy de src/ que solo contienen stubs
# VERIFICACIÓN: Confirmar que cada archivo es un stub antes de eliminar

echo "=== Verificando que todos son stubs ==="
for f in $(find src/api src/core src/dashboard src/data src/monitoring src/strategies src/utils -name "*.py" -type f); do
  lines=$(wc -l < "$f")
  if [ "$lines" -gt 2 ]; then
    echo "ADVERTENCIA: $f tiene $lines líneas - NO es stub, revisar manualmente"
  else
    echo "OK (stub): $f"
  fi
done

# Si la verificación es correcta (todos stubs), proceder:

# Eliminar src/api/ (stub - real está en src/presentation/api/)
git rm -r src/api/

# Eliminar src/core/ (stub - real está en src/application/orchestration/)
git rm -r src/core/

# Eliminar src/dashboard/ (stub - real está en src/presentation/dashboard/)
git rm -r src/dashboard/

# Eliminar src/data/ (stub - real está en src/infrastructure/persistence/ y external_apis/)
git rm -r src/data/

# Eliminar src/monitoring/ (stub - real está en src/infrastructure/monitoring/)
git rm -r src/monitoring/

# Eliminar src/strategies/ (stub - real está en src/domain/services/)
git rm -r src/strategies/

# Eliminar src/utils/ (stub - real está en src/application/config/ y src/domain/)
git rm -r src/utils/

# Commit fase 2
git add -A
git commit -m "refactor(cleanup): eliminar 7 directorios legacy con stubs

Sprint 2 Issue #1 - Limpieza de stubs del first commit
- Eliminados: src/api/, src/core/, src/dashboard/, src/data/,
  src/monitoring/, src/strategies/, src/utils/
- Todos contenían solo placeholders '# TODO: Implement ...'
- Código real ya existe en estructura Clean Architecture:
  - src/presentation/api/ (implementado)
  - src/application/orchestration/ (implementado)
  - src/presentation/dashboard/ (implementado)
  - src/infrastructure/ (implementado)
  - src/domain/services/ (implementado)"
```

### Fase 3: Eliminar directorio config/ duplicado

```bash
# 5. Eliminar config/ completo (usar solo configs/)
# Los archivos de config/ son templates con PLACEHOLDER
# Los archivos de configs/ son las configuraciones reales

# Verificar que configs/ tiene todos los 10 bots
echo "=== Verificando configs/ ==="
ls -1 configs/bot_*.yaml | wc -l  # Debe ser 10

# Eliminar config/ completo
git rm -r config/

# Commit fase 3
git add -A
git commit -m "refactor(config): eliminar directorio config/ duplicado

Sprint 2 Issue #1 - Consolidación de configuraciones
- Eliminado: config/ (templates placeholder con bot_id: PLACEHOLDER)
- Fuente única: configs/ (10 YAMLs con configuraciones reales)
- Eliminado: config/prometheus/ (mover a infra/ si necesario)
- Eliminado: config/bots/ (nombres antiguos de stubs)
- Eliminados: config/*.yaml (api_endpoints, capital_allocation, etc.)"
```

### Fase 4: Actualizar imports en archivos movidos

```bash
# 6. Actualizar imports en los bots movidos
# Buscar imports que referencien la ubicación antigua

echo "=== Buscando imports que referencien src.bots ==="
grep -rn "from src.bots" src/ tests/ --include="*.py"
grep -rn "import src.bots" src/ tests/ --include="*.py"
grep -rn "from bots" src/ tests/ --include="*.py"
grep -rn "import bots" src/ tests/ --include="*.py"

# Actualizar cada import encontrado:
# ANTES: from src.bots.base_bot import BaseBotStrategy
# DESPUÉS: from src.application.bots.base_bot import BaseBotStrategy

# Script automático de actualización de imports:
find src/ tests/ -name "*.py" -type f -exec sed -i \
  's/from src\.bots\./from src.application.bots./g' {} +

find src/ tests/ -name "*.py" -type f -exec sed -i \
  's/import src\.bots\./import src.application.bots./g' {} +

# Buscar también referencias a directorios legacy eliminados
echo "=== Buscando referencias a directorios eliminados ==="
grep -rn "from src.api" src/ tests/ --include="*.py"
grep -rn "from src.core" src/ tests/ --include="*.py"
grep -rn "from src.dashboard" src/ tests/ --include="*.py"
grep -rn "from src.data" src/ tests/ --include="*.py"
grep -rn "from src.monitoring" src/ tests/ --include="*.py"
grep -rn "from src.strategies" src/ tests/ --include="*.py"
grep -rn "from src.utils" src/ tests/ --include="*.py"

# Actualizar imports legacy restantes:
find src/ tests/ -name "*.py" -type f -exec sed -i \
  's/from src\.api\./from src.presentation.api./g' {} +
find src/ tests/ -name "*.py" -type f -exec sed -i \
  's/from src\.core\.event_bus/from src.application.orchestration.event_bus/g' {} +
find src/ tests/ -name "*.py" -type f -exec sed -i \
  's/from src\.core\.health_checker/from src.application.orchestration.health_checker/g' {} +
find src/ tests/ -name "*.py" -type f -exec sed -i \
  's/from src\.dashboard\./from src.presentation.dashboard./g' {} +
find src/ tests/ -name "*.py" -type f -exec sed -i \
  's/from src\.monitoring\./from src.infrastructure.monitoring./g' {} +
find src/ tests/ -name "*.py" -type f -exec sed -i \
  's/from src\.data\./from src.infrastructure.persistence./g' {} +
find src/ tests/ -name "*.py" -type f -exec sed -i \
  's/from src\.utils\./from src.domain.utils./g' {} +
find src/ tests/ -name "*.py" -type f -exec sed -i \
  's/from src\.strategies\./from src.domain.services.strategies./g' {} +

# Commit fase 4
git add -A
git commit -m "refactor(imports): actualizar todos los imports a Clean Architecture

Sprint 2 Issue #1 - Actualización de imports
- src.bots.* -> src.application.bots.*
- src.api.* -> src.presentation.api.*
- src.core.* -> src.application.orchestration.*
- src.dashboard.* -> src.presentation.dashboard.*
- src.monitoring.* -> src.infrastructure.monitoring.*
- src.data.* -> src.infrastructure.persistence.*
- src.utils.* -> src.domain.utils.*
- src.strategies.* -> src.domain.services.strategies.*"
```

### Fase 5: Validación y verificación post-migración

```bash
# 7. Verificación post-migración
echo "=== VERIFICACIÓN POST-MIGRACIÓN ==="

# Verificar que no quedan directorios legacy
echo "--- Directorios que NO deben existir ---"
for dir in src/api src/core src/dashboard src/data src/monitoring src/strategies src/utils src/bots config; do
  if [ -d "$dir" ]; then
    echo "ERROR: $dir todavía existe"
  else
    echo "OK: $dir eliminado correctamente"
  fi
done

# Verificar que los bots están en la ubicación correcta
echo "--- Bots en ubicación correcta ---"
ls -1 src/application/bots/bot_*.py | wc -l  # Debe ser 10
ls -1 src/application/bots/base_bot.py       # Debe existir
ls -1 src/application/bots/bot_manager.py    # Debe existir

# Verificar estructura Clean Architecture
echo "--- Estructura Clean Architecture ---"
echo "domain/:"     && ls src/domain/
echo "application/:" && ls src/application/
echo "infrastructure/:" && ls src/infrastructure/
echo "presentation/:"   && ls src/presentation/

# Verificar que configs/ está completo
echo "--- Configuraciones ---"
ls -1 configs/bot_*.yaml | wc -l  # Debe ser 10

# Verificar que no quedan imports rotos
echo "--- Buscando imports rotos ---"
grep -rn "from src.bots\." src/ tests/ --include="*.py" && echo "ERROR: imports legacy encontrados" || echo "OK: sin imports legacy"
grep -rn "from src.api\." src/ tests/ --include="*.py" && echo "ERROR" || echo "OK"
grep -rn "from src.core\." src/ tests/ --include="*.py" && echo "ERROR" || echo "OK"
grep -rn "from src.dashboard\." src/ tests/ --include="*.py" && echo "ERROR" || echo "OK"
grep -rn "from src.data\." src/ tests/ --include="*.py" && echo "ERROR" || echo "OK"
grep -rn "from src.monitoring\." src/ tests/ --include="*.py" && echo "ERROR" || echo "OK"
grep -rn "from src.strategies\." src/ tests/ --include="*.py" && echo "ERROR" || echo "OK"
grep -rn "from src.utils\." src/ tests/ --include="*.py" && echo "ERROR" || echo "OK"

# Ejecutar tests para verificar que nada se rompió
echo "--- Ejecutando tests ---"
python -m pytest tests/ -v --tb=short 2>&1 | tail -20

# Verificar tipos con mypy
echo "--- Verificando tipos ---"
python -m mypy src/ --ignore-missing-imports 2>&1 | tail -10
```

### Fase 6: Actualizar documentación y hacer push

```bash
# 8. Actualizar contexto_proyecto.md con nueva estructura
# (Actualizar la sección ARQUITECTURA EN TRANSICIÓN)
# Cambiar estado de "Con Directorios Legacy" a "Clean Architecture Completa"

# Commit fase 6
git add -A
git commit -m "docs(contexto): actualizar arquitectura a Clean Architecture completa

Sprint 2 Issue #1 - Documentación actualizada
- Arquitectura: transición completada
- Directorios legacy: eliminados
- Estructura: 100% Clean Architecture"

# 9. Push y crear Pull Request
git push origin refactor/sprint2-clean-architecture

# 10. Crear PR desde GitHub (o con gh cli)
gh pr create \
  --title "refactor: Sprint 2 - Migración completa a Clean Architecture" \
  --body "## Sprint 2 - Issue #1: Migración a Clean Architecture

### Cambios realizados:
- Movidos 10 bots + base_bot + bot_manager a src/application/bots/
- Eliminados 7 directorios legacy con stubs (src/api, core, dashboard, data, monitoring, strategies, utils)
- Eliminado config/ duplicado (fuente única: configs/)
- Actualizados todos los imports
- Tests verificados

### Estructura resultante:
- src/domain/ (lógica de negocio)
- src/application/ (casos de uso + bots)
- src/infrastructure/ (implementaciones)
- src/presentation/ (API + dashboard)

Closes #1 (Sprint 2)" \
  --base main
```

---

## 4. RESUMEN EJECUTIVO

### Estadísticas de la Migración

| Métrica | Valor |
|---|---|
| Archivos movidos (código real) | 13 (10 bots + base_bot + bot_manager + __init__) |
| Directorios eliminados (stubs) | 7 en src/ + 1 config/ = 8 total |
| Archivos stub eliminados | ~50+ archivos placeholder |
| Config templates eliminados | 10 YAMLs + 5 archivos generales |
| Commits de migración | 6 (uno por fase) |
| Imports a actualizar | Depende del grep (ejecutar fase 4) |

### Riesgos y Mitigaciones

| Riesgo | Mitigación |
|---|---|
| Imports rotos tras mover bots | Script sed automático + grep de verificación |
| Tests fallando | Ejecutar pytest en fase 5 antes de push |
| Perder código real | Verificación pre-eliminación (script línea 2+) |
| CI/CD roto | Los workflows ya apuntan a paths correctos |
| Rollback necesario | Rama separada, main intacto hasta merge PR |

### Buenas Prácticas Aplicadas

1. **Rama dedicada:** `refactor/sprint2-clean-architecture` (no tocar main)
2. **Commits atómicos:** Un commit por fase para facilitar rollback parcial
3. **Verificación pre-eliminación:** Script que detecta archivos no-stub
4. **Verificación post-migración:** Tests + mypy + grep de imports rotos
5. **Pull Request:** Revisión antes de merge a main
6. **Mensajes de commit:** Formato conventional commits en español

### Orden de Ejecución Recomendado

```
Fase 1: Mover bots reales        (~5 min)
Fase 2: Eliminar stubs legacy    (~3 min)
Fase 3: Eliminar config/         (~2 min)
Fase 4: Actualizar imports       (~10 min, revisar manualmente)
Fase 5: Validación completa      (~5 min)
Fase 6: Documentación + PR       (~5 min)
-------------------------------------------
Total estimado:                   ~30 min
```

---

**Documento generado:** 2026-02-15
**Issue de referencia:** #1 - Auditoría Completa del Proyecto
**Sprint:** 2 de 4
**Autor:** Sistema AI (verificación manual requerida antes de ejecución)
