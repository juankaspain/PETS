# 🪟 PETS - Guía Completa para Windows + Git Bash

**Sistema Operativo:** Windows 10/11  
**Terminal:** Git Bash (NO PowerShell, NO CMD)  
**Python:** 3.11+

---

## 📋 TABLA DE CONTENIDOS

1. [Prerequisites](#prerequisites)
2. [Instalación Python](#instalación-python)
3. [Configuración Git Bash](#configuración-git-bash)
4. [Clonar Repositorio](#clonar-repositorio)
5. [Entorno Virtual](#entorno-virtual)
6. [Configuración .env](#configuración-env)
7. [Estructura Directorios](#estructura-directorios)
8. [Ejecutar Paper Trading](#ejecutar-paper-trading)
9. [Lanzar Dashboard](#lanzar-dashboard)
10. [Verificación](#verificación)
11. [Monitoreo Diario](#monitoreo-diario)
12. [Troubleshooting Windows](#troubleshooting-windows)

---

## 📦 PREREQUISITES

### Componentes Necesarios

- ✅ **Windows 10/11** (64-bit)
- ✅ **Git Bash** (incluido con Git for Windows)
- ✅ **Python 3.11+** (instalador oficial)
- ✅ **8GB+ RAM** (16GB recomendado)
- ✅ **10GB+ espacio disco**

---

## 🐍 INSTALACIÓN PYTHON

### Paso 1.1: Descargar Python

1. Ir a: https://www.python.org/downloads/
2. Descargar **Python 3.11.x** o superior (64-bit)
3. **IMPORTANTE:** Durante instalación marcar:
   - ☑️ **"Add Python to PATH"** (CRÍTICO)
   - ☑️ "Install pip"
   - ☑️ "Install for all users" (opcional)

### Paso 1.2: Verificar Instalación

**Abrir Git Bash** (NO PowerShell, NO CMD):

```bash
# Verificar Python instalado
python --version
# Debe mostrar: Python 3.11.x

# Si no funciona, probar:
python3 --version
py --version

# Verificar pip
pip --version
# Debe mostrar: pip 23.x.x from ...
```

**⚠️ PROBLEMA COMÚN:**

Si `python` no funciona:

```bash
# Opción A: Usar 'py' (Python Launcher)
py --version

# Opción B: Agregar a PATH manualmente
# 1. Buscar donde está Python:
where python
# O:
where py

# 2. Agregar a PATH en Git Bash (~/.bashrc):
echo 'export PATH="/c/Users/TuUsuario/AppData/Local/Programs/Python/Python311:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**✅ CHECKPOINT:** `python --version` muestra 3.11+

---

## 🔧 CONFIGURACIÓN GIT BASH

### Paso 2.1: Instalar Git Bash (si no lo tienes)

1. Descargar: https://git-scm.com/download/win
2. Instalar con opciones por defecto
3. Abrir "Git Bash" desde menú inicio

### Paso 2.2: Configurar Alias (Opcional pero Útil)

```bash
# Abrir archivo configuración
vim ~/.bashrc
# O si no sabes vim:
nano ~/.bashrc

# Agregar al final:
alias python='python.exe'
alias pip='pip.exe'
alias ls='ls --color=auto'
alias ll='ls -lh'

# Guardar y cerrar
# vim: :wq
# nano: Ctrl+O, Enter, Ctrl+X

# Recargar config
source ~/.bashrc
```

### Paso 2.3: Verificar Git Bash Funcional

```bash
# Verificar shell
echo $SHELL
# Debe mostrar: /usr/bin/bash o similar

# Verificar comandos Unix
ls -lh
pwd
which python
```

**✅ CHECKPOINT:** Comandos Unix funcionan en Git Bash

---

## 📂 CLONAR REPOSITORIO

### Paso 3.1: Navegar a Directorio Deseado

```bash
# Ir a tu carpeta de proyectos
# WINDOWS PATH: C:\Users\TuUsuario\Documents\Proyectos
# GIT BASH PATH: /c/Users/TuUsuario/Documents/Proyectos

cd /c/Users/TuUsuario/Documents

# Crear carpeta proyectos si no existe
mkdir -p Proyectos
cd Proyectos
```

**⚠️ IMPORTANTE WINDOWS PATHS:**

```bash
# ❌ MAL (Windows style):
cd C:\Users\TuUsuario\Documents

# ✅ BIEN (Git Bash style):
cd /c/Users/TuUsuario/Documents

# Conversión:
# C:\ → /c/
# D:\ → /d/
# Backslash \ → Forward slash /
```

### Paso 3.2: Clonar PETS

```bash
# Clonar repositorio
git clone https://github.com/juankaspain/PETS.git

# Entrar al directorio
cd PETS

# Verificar archivos
ls -lh

# Actualizar a última versión
git checkout main
git pull origin main
```

**✅ CHECKPOINT:** Directorio PETS creado con archivos

---

## 🐍 ENTORNO VIRTUAL

### Paso 4.1: Crear Entorno Virtual

```bash
# ASEGÚRATE ESTAR EN DIRECTORIO PETS
pwd
# Debe mostrar: /c/Users/TuUsuario/.../PETS

# Crear venv
python -m venv venv

# Si falla, probar:
py -m venv venv
# O:
python3 -m venv venv
```

**Deberías ver carpeta `venv/` creada:**

```bash
ls -lh venv/
# Debe mostrar:
# drwxr-xr-x Scripts/
# drwxr-xr-x Lib/
# -rw-r--r-- pyvenv.cfg
```

### Paso 4.2: Activar Entorno Virtual (GIT BASH)

**⚠️ CRÍTICO EN WINDOWS + GIT BASH:**

```bash
# FORMA CORRECTA EN GIT BASH:
source venv/Scripts/activate

# ❌ NO funciona en Git Bash:
# venv\Scripts\activate (Windows CMD)
# venv\Scripts\Activate.ps1 (PowerShell)
```

**Verificar activación:**

```bash
# Debe aparecer (venv) en prompt:
# (venv) user@DESKTOP-XXX MINGW64 /c/Users/.../PETS

# Verificar Python apunta a venv:
which python
# Debe mostrar: /c/Users/.../PETS/venv/Scripts/python

# Verificar pip del venv:
which pip
# Debe mostrar: /c/Users/.../PETS/venv/Scripts/pip
```

**✅ CHECKPOINT:** Prompt muestra `(venv)` al inicio

### Paso 4.3: Instalar Dependencias

```bash
# Actualizar pip primero
pip install --upgrade pip

# Instalar dependencias proyecto
pip install -r requirements.txt

# ESTO TOMARÁ 5-10 MINUTOS
# Verás instalación de: streamlit, fastapi, web3, pydantic, etc.
```

**Verificar instalación crítica:**

```bash
pip list | grep streamlit
pip list | grep fastapi
pip list | grep pydantic
pip list | grep web3

# Todos deben aparecer con versiones
```

**✅ CHECKPOINT:** Dependencias instaladas sin errores

---

## 🔐 CONFIGURACIÓN .ENV

### Paso 5.1: Copiar Template

```bash
# Desde directorio PETS/
cp .env.example .env

# Verificar creado
ls -lh .env
```

### Paso 5.2: Editar .env (WINDOWS)

**Opción A: Editor Git Bash (nano/vim)**

```bash
nano .env
# O:
vim .env
```

**Opción B: Notepad++ (recomendado Windows)**

```bash
# Abrir con Notepad++ (si instalado)
notepad++ .env

# O Notepad estándar:
notepad.exe .env

# O VS Code:
code .env
```

### Paso 5.3: Configuración MÍNIMA (Copiar/Pegar)

**IMPORTANTE:** Usar **forward slashes** `/` en paths, NO backslashes `\`

```bash
# ========================================
# CONFIGURACIÓN PAPER TRADING WINDOWS
# ========================================

# Blockchain (público)
POLYGON_RPC_URL=https://polygon-rpc.com
POLYGON_CHAIN_ID=137

# Wallet (DUMMY - no se usa en paper trading)
HOT_WALLET_PRIVATE_KEY=0x0000000000000000000000000000000000000000000000000000000000000001
HOT_WALLET_PERCENTAGE=15
ENCRYPTION_KEY=dummy-key-paper-only

# Database (SQLite local)
DATABASE_URL=sqlite:///./pets_paper_trading.db
TIMESCALEDB_CHUNK_INTERVAL=7 days
TIMESCALEDB_COMPRESSION_AFTER=14 days

# Redis (opcional)
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# Polymarket API
POLYMARKET_API_URL=https://clob.polymarket.com
POLYMARKET_WS_URL=wss://ws-subscriptions-clob.polymarket.com

# Circuit Breakers
MAX_CONSECUTIVE_LOSSES=3
MAX_DAILY_LOSS_PCT=5.0
MAX_BOT_DRAWDOWN_PCT=25.0
MAX_PORTFOLIO_DRAWDOWN_PCT=40.0

# Bot 8 Config
BOT8_SPREAD_THRESHOLD=0.15
BOT8_ENTRY_LOW=0.20
BOT8_ENTRY_HIGH=0.80
BOT8_HOLD_HOURS_MIN=24
BOT8_HOLD_HOURS_MAX=48
BOT8_TARGET_DELTA=0.30
BOT8_STOP_LOSS_PCT=0.10

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
METRICS_EXPORT_PORT=8001

# API
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
FASTAPI_WORKERS=1

# Dashboard
STREAMLIT_PORT=8501

# Logging (usar forward slashes)
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=logs/pets.log

# Security
ALLOWED_ORIGINS=http://localhost:8501,http://localhost:8000
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

**Guardar archivo:**
- **Notepad++/VS Code:** Ctrl+S
- **nano:** Ctrl+O → Enter → Ctrl+X
- **vim:** Esc → `:wq` → Enter

**✅ CHECKPOINT:** Archivo `.env` guardado

---

## 📁 ESTRUCTURA DIRECTORIOS

### Paso 6.1: Crear Directorios

```bash
# Desde directorio PETS/
mkdir -p logs
mkdir -p logs/paper_trading_reports
mkdir -p data
mkdir -p data/cache

# Verificar creados
ls -lh logs/
ls -lh data/
```

**⚠️ NO necesitas `chmod` en Windows** (permisos diferentes)

**✅ CHECKPOINT:** Directorios creados

---

## 🚀 EJECUTAR PAPER TRADING

### Paso 7.1: Ventana Git Bash #1 - Bot Trading

**Abrir Git Bash nueva ventana:**

1. Click derecho en escritorio → "Git Bash Here"
2. O: Inicio → Git Bash

```bash
# Navegar a PETS
cd /c/Users/TuUsuario/Documents/Proyectos/PETS

# Activar venv
source venv/Scripts/activate

# Verificar prompt (venv)
echo "(venv) activado: OK"

# Verificar desde raíz
pwd
# Debe mostrar: /c/Users/.../PETS
```

### Paso 7.2: EJECUTAR Bot 8

```bash
# Ejecución en primer plano (recomendado primera vez)
python scripts/run_bot8_paper_trading.py

# Deberías ver:
# ================================================================================
# BOT 8 PAPER TRADING VALIDATION - STARTING
# ================================================================================
# Duration: 30 days simulation
# Initial Balance: $5,000
# ...
```

**⚠️ DEJAR ESTA VENTANA ABIERTA** - NO cerrar

### Paso 7.3: Ejecución Background (Alternativa Windows)

**Git Bash NO soporta nohup bien en Windows. Alternativas:**

**Opción A: Screen/tmux (requiere instalación adicional)**

```bash
# NO recomendado en Windows - complica setup
```

**Opción B: Ejecutar en ventana separada persistente**

```bash
# Crear script launcher
cat > run_bot8.sh << 'EOF'
#!/bin/bash
cd /c/Users/TuUsuario/Documents/Proyectos/PETS
source venv/Scripts/activate
python scripts/run_bot8_paper_trading.py > logs/bot8_stdout.log 2>&1
EOF

chmod +x run_bot8.sh

# Ejecutar en nueva ventana Git Bash y minimizar
./run_bot8.sh
```

**Opción C: Python en background (RECOMENDADO WINDOWS)**

```bash
# Usar pythonw.exe (Windows background mode)
pythonw.exe scripts/run_bot8_paper_trading.py &

# Ver proceso
tasklist | grep python
```

**Recomendación:** Primera vez usar **primer plano** para ver logs directos.

**✅ CHECKPOINT:** Bot corriendo, ves logs en consola

---

## 📊 LANZAR DASHBOARD

### Paso 8.1: Ventana Git Bash #2 - Dashboard

**Abrir SEGUNDA ventana Git Bash:**

```bash
# Navegar a PETS
cd /c/Users/TuUsuario/Documents/Proyectos/PETS

# Activar MISMO venv
source venv/Scripts/activate

# Verificar venv activo
which python
# Debe mostrar: /c/Users/.../PETS/venv/Scripts/python
```

### Paso 8.2: Verificar Streamlit

```bash
streamlit --version
# Debe mostrar: Streamlit, version X.X.X

# Si falla:
pip install streamlit
```

### Paso 8.3: Lanzar Dashboard

```bash
# Navegar a directorio dashboard
cd src/presentation/dashboard

# Ejecutar Streamlit
streamlit run app.py --server.port 8501

# Deberías ver:
#   You can now view your Streamlit app in your browser.
#
#   Local URL: http://localhost:8501
#   Network URL: http://192.168.X.X:8501
```

### Paso 8.4: Abrir en Navegador

**El navegador debería abrirse automáticamente.**

Si no:

```bash
# Windows - abrir navegador desde Git Bash:
start http://localhost:8501

# O manualmente:
# Abre Chrome/Firefox/Edge
# Navega a: http://localhost:8501
```

**✅ CHECKPOINT:** Dashboard visible en navegador

---

## ✅ VERIFICACIÓN

### Estado Actual (2 Ventanas Git Bash Abiertas)

**Ventana 1: Paper Trading Bot**
```
(venv) user@DESKTOP MINGW64 /c/Users/.../PETS
$ python scripts/run_bot8_paper_trading.py

2026-02-13 03:34:00 - bot8_paper_trading_initialized
2026-02-13 03:34:00 - session_started
2026-02-13 03:34:05 - signal_detected: market=TRUMP2024, price=0.15
...
```

**Ventana 2: Dashboard**
```
(venv) user@DESKTOP MINGW64 /c/Users/.../PETS/src/presentation/dashboard
$ streamlit run app.py --server.port 8501

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
...
```

**Navegador: http://localhost:8501**

```
┌────────────────────────────────────────────────────────┐
│ PETS Dashboard - Bot 8 Paper Trading                  │
├────────────────────────────────────────────────────────┤
│ 📊 Overview                                            │
│                                                         │
│ ┌──────────────┬──────────────┬──────────────┐        │
│ │ Total ROI    │ Sharpe Ratio │ Max Drawdown │        │
│ │ +2.5% ⬆️     │ 0.65         │ -3.2%        │        │
│ └──────────────┴──────────────┴──────────────┘        │
│                                                         │
│ [Actualizado hace 2s]                                  │
└────────────────────────────────────────────────────────┘
```

### Verificar Logs Paper Trading

**Ventana Git Bash #3 (nueva o usa #1 temporalmente):**

```bash
cd /c/Users/TuUsuario/Documents/Proyectos/PETS

# Ver logs en tiempo real
tail -f logs/bot8_paper_trading.log

# Salir: Ctrl+C
```

### Verificar Reportes Diarios

```bash
# Listar reportes
ls -lh logs/paper_trading_reports/

# Ver último reporte
cat logs/paper_trading_reports/bot8_day_01.json | python -m json.tool

# Salida esperada:
{
  "day": 1,
  "date": "2026-02-13T03:34:00Z",
  "balance": 5085.00,
  "day_pnl": 85.00,
  "trades_count": 2,
  "win_rate_pct": 50.00,
  ...
}
```

**✅ CHECKPOINT COMPLETO:**
- ✅ Bot 8 corriendo (Ventana #1)
- ✅ Dashboard activo (Ventana #2)
- ✅ Navegador mostrando métricas
- ✅ Logs generándose
- ✅ Reportes creándose

---

## 📈 MONITOREO DIARIO

### Rutina Diaria (5 min) - Git Bash

```bash
# 1. Verificar bot sigue corriendo
tasklist | findstr python
# Debe mostrar: python.exe  PID  ...

# O ver ventana Git Bash #1 activa con logs

# 2. Ver reporte día anterior
cd /c/Users/TuUsuario/Documents/Proyectos/PETS
cat logs/paper_trading_reports/bot8_day_$(date +%d -d yesterday).json | python -m json.tool

# 3. Abrir dashboard
start http://localhost:8501

# 4. Revisar métricas clave:
# - Win rate trending hacia >52%
# - Drawdown <15%
# - No circuit breakers triggered
```

### Gestión Procesos Windows

**Ver procesos Python:**

```bash
# Listar todos procesos Python
tasklist | findstr python

# Ver detalles:
tasklist /FI "IMAGENAME eq python.exe" /V
```

**Detener bot si necesario:**

```bash
# Opción A: Ctrl+C en ventana Git Bash #1

# Opción B: Kill por nombre (CUIDADO - mata todos Python)
taskkill /IM python.exe /F

# Opción C: Kill por PID (recomendado)
# 1. Obtener PID:
tasklist | findstr python
# Ejemplo salida: python.exe  12345  Console  ...

# 2. Kill específico:
taskkill /PID 12345 /F
```

**Reiniciar bot:**

```bash
# Volver a Ventana #1 Git Bash
cd /c/Users/TuUsuario/Documents/Proyectos/PETS
source venv/Scripts/activate
python scripts/run_bot8_paper_trading.py
```

---

## 🔧 TROUBLESHOOTING WINDOWS

### Error: `python: command not found` (Git Bash)

```bash
# Opción A: Usar 'py'
py --version
py scripts/run_bot8_paper_trading.py

# Opción B: Usar python.exe explícito
python.exe --version
python.exe scripts/run_bot8_paper_trading.py

# Opción C: Agregar a PATH en .bashrc
echo 'export PATH="/c/Users/TuUsuario/AppData/Local/Programs/Python/Python311:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Error: `ModuleNotFoundError: No module named 'src'`

```bash
# CAUSA: No estás en directorio raíz PETS

# SOLUCIÓN:
cd /c/Users/TuUsuario/Documents/Proyectos/PETS
pwd  # Verificar
python scripts/run_bot8_paper_trading.py
```

### Error: `No such file or directory: 'venv/Scripts/activate'`

```bash
# CAUSA: venv no creado o ruta incorrecta

# VERIFICAR venv existe:
ls -lh venv/Scripts/

# Si no existe, crear:
python -m venv venv

# Activar (GIT BASH - NO Windows CMD):
source venv/Scripts/activate
```

### Error: `Port 8501 already in use`

```bash
# Ver qué usa puerto 8501:
netstat -ano | findstr :8501

# Salida ejemplo:
# TCP  0.0.0.0:8501  0.0.0.0:0  LISTENING  12345
#                                          ^^^^^ PID

# Matar proceso:
taskkill /PID 12345 /F

# Reintentar dashboard:
streamlit run app.py --server.port 8501
```

### Error: Dashboard muestra "Connecting..." infinito

```bash
# 1. Verificar bot corriendo:
tasklist | findstr python

# 2. Verificar logs bot:
tail -f logs/bot8_paper_trading.log
# Debe mostrar actividad reciente

# 3. Firewall Windows bloqueando?
# → Permitir Python en Firewall Windows
# → Panel Control → Firewall → Allow app
# → Add python.exe

# 4. Reiniciar ambos:
# Ventana #1: Ctrl+C → relanzar bot
# Ventana #2: Ctrl+C → relanzar dashboard
```

### Error: `PermissionError` al escribir logs

```bash
# CAUSA: Antivirus/Permisos Windows

# SOLUCIÓN A: Ejecutar Git Bash como Administrador
# Click derecho → "Run as administrator"

# SOLUCIÓN B: Cambiar directorio logs
# Editar .env:
LOG_FILE=C:/Users/TuUsuario/Documents/PETS/logs/pets.log

# SOLUCIÓN C: Deshabilitar antivirus temporalmente (desarrollo)
```

### Problema: Line endings CRLF vs LF

```bash
# SÍNTOMA: Errores raros en scripts

# SOLUCIÓN: Configurar Git para Windows
git config --global core.autocrlf true

# Reconvertir archivos:
git rm --cached -r .
git reset --hard
```

---

## 🎯 CHECKLIST FINAL WINDOWS

### Antes de Empezar

- [ ] Python 3.11+ instalado
- [ ] "Add to PATH" marcado en instalación Python
- [ ] Git Bash instalado y funcional
- [ ] 10GB+ espacio disco libre
- [ ] Antivirus no bloqueando Python

### Configuración Completada

- [ ] Repositorio clonado en `/c/Users/.../PETS`
- [ ] Entorno virtual creado (`venv/` existe)
- [ ] venv activado (`(venv)` en prompt)
- [ ] Dependencias instaladas (`pip list` muestra streamlit, etc.)
- [ ] Archivo `.env` configurado (copiar/pegar config mínima)
- [ ] Directorios `logs/` y `data/` creados

### Sistema Funcionando

- [ ] **Ventana Git Bash #1:** Bot corriendo, logs visibles
- [ ] **Ventana Git Bash #2:** Dashboard corriendo, URL visible
- [ ] **Navegador:** Dashboard en http://localhost:8501 cargado
- [ ] Métricas actualizándose cada 1-2 segundos
- [ ] Archivos en `logs/paper_trading_reports/` generándose

### Monitoreo Activo

- [ ] Dashboard accesible todos los días
- [ ] Reportes diarios revisados
- [ ] No errores críticos en logs
- [ ] Bot corre continuo 24/7

---

## 🆘 SOPORTE WINDOWS

### Recursos Específicos Windows

**Python Windows:**
- https://docs.python.org/3/using/windows.html
- https://www.python.org/downloads/windows/

**Git Bash:**
- https://git-scm.com/download/win
- https://www.atlassian.com/git/tutorials/git-bash

**Streamlit Windows:**
- https://docs.streamlit.io/get-started/installation/windows

### Comandos Útiles Git Bash en Windows

```bash
# Abrir explorador Windows en directorio actual
explorer.exe .

# Abrir archivo con programa predeterminado
start archivo.txt

# Ver información sistema
systeminfo | head -20

# Limpiar pantalla
clear
# O: Ctrl+L

# Historial comandos
history

# Buscar en historial
history | grep python
```

---

## 📞 PRÓXIMOS PASOS

**AHORA deberías tener (Windows + Git Bash):**

✅ **2 Ventanas Git Bash abiertas:**
- Ventana #1: Bot 8 corriendo con logs visibles
- Ventana #2: Streamlit dashboard activo

✅ **Navegador:**
- Dashboard en http://localhost:8501
- Métricas actualizándose en vivo

✅ **Sistema paper trading:**
- Sin wallet real (CERO riesgo)
- Simulación 30 días automática
- Reportes diarios generándose

---

**¿TODO FUNCIONANDO?** Confirma que ves:
1. Logs bot en Ventana #1
2. Dashboard cargado en navegador
3. Métricas actualizándose

Y te explico el siguiente paso de monitoreo diario.

---

**Last Updated:** 2026-02-13  
**Version:** 1.0 Windows  
**Tested:** Windows 10/11 + Git Bash + Python 3.11