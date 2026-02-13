# Bot 8 Paper Trading Validation Guide

**Objetivo:** Validar Bot 8 Tail Risk strategy con 30 días paper trading antes de live deployment.

**Evidencia Histórica:** $106K profits documentados  
**Validation Targets:**
- Win rate: >52%
- Sharpe ratio: >0.8
- Max drawdown: <15%
- Min trades: 50

---

## 📋 PREREQUISITES

### 1. Environment Setup

```bash
# Check Python version (3.11+ required)
python --version

# Verify repository
cd /path/to/PETS
git status
git pull origin main
```

### 2. Dependencies

```bash
# Install dependencies
pip install -r requirements.txt

# Verify key packages
pip list | grep -E "web3|asyncio|pydantic|timescale|redis|streamlit|fastapi"
```

### 3. Configuration Verification

```bash
# Verify Bot 8 config exists
ls -lh configs/bots/bot_8_config.yaml

# Review config (optional)
cat configs/bots/bot_8_config.yaml
```

**Expected config values:**
- Strategy: `TAIL_RISK`
- Zones: `[1, 2]` (Z3-Z5 prohibited)
- Kelly: `0.25` (Half Kelly)
- Order type: `POST_ONLY`
- Capital: `5000` (paper trading balance)
- Max position: `1000`

### 4. Directory Structure

```bash
# Create logs directory
mkdir -p logs/paper_trading_reports

# Verify script exists
ls -lh scripts/run_bot8_paper_trading.py
```

---

## 🚀 EXECUTION

### Pre-flight Checks

```bash
# 1. Check no conflicts
git status  # Should be clean

# 2. Verify tests pass (optional)
pytest tests/ -v --tb=short

# 3. Check disk space
df -h  # Need ~100MB for logs

# 4. Verify network (if using real market data)
ping api.polymarket.com
```

### Launch Paper Trading Session

```bash
# Execute validation script
python scripts/run_bot8_paper_trading.py
```

**Expected output:**
```
================================================================================
BOT 8 PAPER TRADING VALIDATION - STARTING
================================================================================
Duration: 30 days simulation
Initial Balance: $5,000
Strategy: Tail Risk (Z1-Z2 only)
Targets: Win rate >52%, Sharpe >0.8, Drawdown <15%
================================================================================

2026-02-13 03:26:00 - bot8_paper_trading_initialized
2026-02-13 03:26:00 - session_started
2026-02-13 03:26:00 - day_started: day=1, total_days=30
...
```

### Background Execution (Optional)

```bash
# Run in background with nohup
nohup python scripts/run_bot8_paper_trading.py > logs/bot8_stdout.log 2>&1 &

# Get process ID
echo $!

# Tail logs
tail -f logs/bot8_paper_trading.log
```

### Graceful Shutdown

```bash
# Press Ctrl+C in foreground
# OR
kill -SIGINT <PID>  # Graceful shutdown

# Force kill (last resort)
kill -9 <PID>
```

---

## 📊 MONITORING

### Real-Time Dashboard

```bash
# Launch Streamlit dashboard (separate terminal)
cd src/presentation/dashboard
streamlit run app.py

# Access dashboard
# Browser: http://localhost:8501
```

**Dashboard pages to monitor:**
1. **Overview:** Real-time portfolio metrics
2. **Bot Control:** Bot 8 status and state
3. **Performance:** ROI chart and Sharpe tracking
4. **Positions:** Active positions
5. **Risk Monitor:** Zone exposure + circuit breakers

### Daily Reports

```bash
# View latest daily report
cat logs/paper_trading_reports/bot8_day_01.json | jq

# List all reports
ls -lt logs/paper_trading_reports/bot8_day_*.json

# Watch for new reports
watch -n 60 'ls -lt logs/paper_trading_reports/ | head -10'
```

**Daily report format:**
```json
{
  "day": 1,
  "date": "2026-02-13T03:26:00Z",
  "balance": 5125.50,
  "day_pnl": 125.50,
  "total_pnl": 125.50,
  "trades_count": 3,
  "win_rate_pct": 66.67,
  "sharpe_ratio": 0.45,
  "max_drawdown_pct": 2.15,
  "current_drawdown_pct": 0.00
}
```

### Progress Tracking

```bash
# Grep progress from logs
grep "session_progress" logs/bot8_paper_trading.log | tail -5

# Example output:
# 2026-02-13 - session_progress: day=5, progress_pct=16.7, trades=15, win_rate=53.33
# 2026-02-13 - session_progress: day=10, progress_pct=33.3, trades=28, win_rate=53.57
```

### Key Metrics to Watch

**Daily:**
- `win_rate_pct` trending toward >52%
- `sharpe_ratio` increasing toward >0.8
- `max_drawdown_pct` staying <15%
- `trades_count` accumulating (need ≥50)

**Weekly:**
- Consistency of returns (not just lucky streak)
- Circuit breaker activations (should be minimal)
- Position sizing adherence (max $1000)
- Zone compliance (Z1-Z2 only)

---

## 📈 DAILY OPERATIONS

### Morning Routine (Recommended)

```bash
# 1. Check session still running
ps aux | grep run_bot8_paper_trading

# 2. Review yesterday's report
cat logs/paper_trading_reports/bot8_day_$(date -d yesterday +%d).json | jq

# 3. Check for errors
grep -i "error" logs/bot8_paper_trading.log | tail -10

# 4. Verify metrics on track
grep "daily_report" logs/bot8_paper_trading.log | tail -1 | jq
```

### Red Flags

**🚨 Immediate attention required:**
- `max_drawdown_pct > 15.0` → Circuit breaker should trigger
- `win_rate_pct < 40.0` after day 10 → Strategy failing
- Multiple `ERROR` logs → System issues
- Process crashed → Need restart

**⚠️ Monitor closely:**
- `win_rate_pct` declining trend
- `sharpe_ratio < 0.5` after day 15
- Frequent circuit breaker activations
- Low trade count (<2 trades/day average)

### Circuit Breaker Handling

**If circuit breaker triggers:**

```bash
# 1. Check which breaker fired
grep "circuit_breaker" logs/bot8_paper_trading.log | tail -5

# 2. Review cause
# - Consecutive losses (3+)
# - Daily loss (5%+)
# - Bot drawdown (25%+)
# - Portfolio drawdown (40%+)

# 3. Action:
# - Paper trading: Let it auto-recover (built-in)
# - Review strategy if repeated triggers
```

---

## 📋 RESULTS ANALYSIS

### Final Report

**After 30 days (or early success):**

```bash
# View final report
cat logs/paper_trading_reports/bot8_final_report.json | jq

# Pretty print summary
jq '.validation' logs/paper_trading_reports/bot8_final_report.json
```

**Final report structure:**
```json
{
  "session_start": "2026-02-13T03:26:00Z",
  "session_end": "2026-03-15T03:26:00Z",
  "duration_days": 30,
  "final_balance": 5850.00,
  "total_pnl": 850.00,
  "roi_pct": 17.00,
  "trades_count": 58,
  "win_rate_pct": 55.17,
  "sharpe_ratio": 0.92,
  "max_drawdown_pct": 12.50,
  "validation": {
    "targets": {
      "win_rate_pct": 52.0,
      "sharpe_ratio": 0.8,
      "max_drawdown_pct": 15.0,
      "min_trades": 50
    },
    "results": {
      "win_rate_met": true,
      "sharpe_met": true,
      "drawdown_met": true,
      "trades_met": true
    },
    "passed": true
  }
}
```

### Validation Decision Tree

```
validation.passed == true?
├─ YES → ✅ GO LIVE (Fase 15)
│  ├─ Setup hot wallet
│  ├─ Mainnet configuration
│  ├─ Start with reduced capital ($1K-$2K)
│  └─ Monitor closely first week
│
└─ NO → ⚠️ ADJUST & RETRY
   ├─ Analyze failure point:
   │  ├─ win_rate_met == false?
   │  │  → Review signal quality, edge estimation
   │  ├─ sharpe_met == false?
   │  │  → Check volatility, position sizing
   │  ├─ drawdown_met == false?
   │  │  → Reduce Kelly fraction, tighter stops
   │  └─ trades_met == false?
   │     → Review opportunity detection, filters
   │
   ├─ Adjust config:
   │  └─ Edit configs/bots/bot_8_config.yaml
   │
   └─ Re-run validation:
      └─ python scripts/run_bot8_paper_trading.py
```

---

## ✅ GO LIVE CHECKLIST

**If `validation.passed == true`:**

### Phase 15 Preparation

```bash
# 1. Archive paper trading results
cp -r logs/paper_trading_reports logs/bot8_paper_trading_archive_$(date +%Y%m%d)

# 2. Review final report one more time
cat logs/paper_trading_reports/bot8_final_report.json | jq '.validation'

# 3. Document decision
echo "Bot 8 validated $(date)" >> docs/deployment_log.md
echo "Win rate: $(jq -r '.win_rate_pct' logs/paper_trading_reports/bot8_final_report.json)%" >> docs/deployment_log.md
```

### Next Steps

1. **Hot Wallet Setup:**
   - Generate BIP39 mnemonic (offline)
   - Fund with small amount ($1K-$2K initially)
   - Test transactions on testnet first

2. **Mainnet Configuration:**
   - Update `.env` with mainnet RPC
   - Configure Polygon mainnet contracts
   - Set gas parameters (EIP-1559)

3. **Risk Limits (Conservative):**
   - Start capital: $1K-$2K (not full $5K)
   - Max position: $500 (reduce from $1K)
   - Circuit breakers: MORE strict first week

4. **Monitoring Enhanced:**
   - Dashboard live connection
   - Alert channels active (email/Slack)
   - Daily manual review mandatory

5. **Incremental Scale:**
   - Week 1: $1K capital, monitor closely
   - Week 2-4: $2K if performance stable
   - Month 2+: Scale to $5K if targets met

---

## ❌ NO-GO ADJUSTMENTS

**If `validation.passed == false`:**

### Diagnosis Workflow

```bash
# 1. Identify failure metric
jq '.validation.results' logs/paper_trading_reports/bot8_final_report.json

# 2. Review daily progression
for f in logs/paper_trading_reports/bot8_day_*.json; do
  echo "$(basename $f): win_rate=$(jq -r '.win_rate_pct' $f), sharpe=$(jq -r '.sharpe_ratio' $f)"
done

# 3. Analyze trade distribution
grep "daily_report" logs/bot8_paper_trading.log | jq -s 'map({day: .day, trades: .trades_count})'
```

### Common Issues & Fixes

**Issue: Win Rate <52%**
- **Diagnosis:** Edge estimation too optimistic
- **Fix:** Increase `min_edge_pct` in config (15% → 18% for Z1)
- **Fix:** Tighten zone filters (remove borderline Z2)
- **Fix:** Add signal confirmation (multiple timeframes)

**Issue: Sharpe Ratio <0.8**
- **Diagnosis:** Returns too volatile
- **Fix:** Reduce position sizes (Kelly 0.25 → 0.20)
- **Fix:** Implement volatility filter (skip high-vol periods)
- **Fix:** Add position correlation limits

**Issue: Max Drawdown >15%**
- **Diagnosis:** Risk management too loose
- **Fix:** Reduce max position size ($1000 → $750)
- **Fix:** Tighter stop losses
- **Fix:** Lower daily loss limit (5% → 3%)

**Issue: Trades <50**
- **Diagnosis:** Too selective, missing opportunities
- **Fix:** Lower `min_edge_pct` slightly (15% → 12% for Z1)
- **Fix:** Expand to more markets
- **Fix:** Increase scan frequency

### Config Adjustment

```bash
# Edit Bot 8 config
vim configs/bots/bot_8_config.yaml

# Example adjustments:
# - base_kelly_fraction: 0.25 → 0.20 (more conservative)
# - min_edge_pct: 15.0 → 18.0 (more selective Z1)
# - max_position_size: 1000 → 750 (reduce risk)
```

### Re-run Validation

```bash
# After config changes
python scripts/run_bot8_paper_trading.py

# Track in separate log
python scripts/run_bot8_paper_trading.py > logs/bot8_retry_$(date +%Y%m%d).log 2>&1
```

---

## 🐛 TROUBLESHOOTING

### Common Errors

**Error: `ModuleNotFoundError: No module named 'src'`**
```bash
# Fix: Run from project root
cd /path/to/PETS
python scripts/run_bot8_paper_trading.py
```

**Error: `FileNotFoundError: bot_8_config.yaml`**
```bash
# Fix: Verify config exists
ls configs/bots/bot_8_config.yaml

# If missing, restore from template
cp configs/bots/bot_8_config.yaml.template configs/bots/bot_8_config.yaml
```

**Error: `ImportError: cannot import name 'TailRiskStrategy'`**
```bash
# Fix: Verify Bot 8 implementation
ls src/bots/bot_08_tail_risk.py

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

**Error: Session crashed mid-run**
```bash
# 1. Check last successful day
ls -lt logs/paper_trading_reports/bot8_day_*.json | head -1

# 2. Review error logs
grep -A 10 "ERROR" logs/bot8_paper_trading.log | tail -20

# 3. Resume not implemented yet - restart from beginning
# TODO: Implement state persistence for resume
```

### Recovery Procedures

**Scenario: Need to restart validation**
```bash
# 1. Archive current attempt
mv logs/paper_trading_reports logs/paper_trading_reports_backup_$(date +%Y%m%d_%H%M)

# 2. Create fresh logs directory
mkdir -p logs/paper_trading_reports

# 3. Restart
python scripts/run_bot8_paper_trading.py
```

**Scenario: System reboot during session**
```bash
# Currently: No auto-resume (TODO: implement state persistence)
# Action: Restart validation from beginning

# Future: State will be saved to Redis/DB for resume
```

---

## 📞 SUPPORT

**Questions or issues:**
- Review logs: `logs/bot8_paper_trading.log`
- Check GitHub issues: https://github.com/juankaspain/PETS/issues
- Documentation: `docs/` directory

**Performance tuning:**
- See: `docs/PERFORMANCE_TUNING.md` (TODO)
- Config reference: `configs/README.md` (TODO)

---

## 📚 REFERENCES

- **Bot 8 Implementation:** `src/bots/bot_08_tail_risk.py`
- **Config Template:** `configs/bots/bot_8_config.yaml`
- **Paper Trading Engine:** `src/infrastructure/paper_trading/paper_trading_engine.py`
- **Dashboard:** `src/presentation/dashboard/app.py`
- **Context Document:** `contexto_proyecto.md`

---

**Last Updated:** 2026-02-13  
**Version:** 1.0  
**Status:** Ready for execution