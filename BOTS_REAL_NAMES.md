# PETS Bot Files - Real Names Mapping

> **CRITICAL DOCUMENT** - Resolves Issues C1-02, C1-03, C5-01, C5-02 from Issue #1
>
> Last Updated: 2025-02-14

## Overview

This document provides the **authoritative mapping** between bot numbers and their **actual file names** in `src/bots/`.

The original `contexto_proyecto.md` documented theoretical bot names that **do not exist** in the repository. This document corrects that discrepancy.

## Bot Files Mapping (REAL)

| Bot # | Strategy Name | **REAL File Name** | Config File |
|-------|---------------|-------------------|-------------|
| Bot 1 | Market Rebalancing | `bot_01_rebalancer.py` + `bot_01_market_rebalancing.py` | `bot_01_rebalancer.yaml` |
| Bot 2 | Esports Trading | `bot_02_esports.py` + `bot_02_esports_parsing.py` | `bot_02_esports.yaml` |
| Bot 3 | Copy Trading | `bot_03_copy_trading.py` | `bot_03_copy_trading.yaml` |
| Bot 4 | News-Driven | `bot_04_news_driven.py` + `bot_04_news_scalping.py` | `bot_04_news_driven.yaml` |
| Bot 5 | Market Making | `bot_05_market_making.py` | `bot_05_market_making.yaml` |
| Bot 6 | Multi-Outcome Arbitrage | `bot_06_multi_outcome.py` + `bot_06_multi_outcome_arb.py` | `bot_06_multi_outcome.yaml` |
| Bot 7 | Contrarian | `bot_07_contrarian.py` + `bot_07_contrarian_attention.py` | `bot_07_contrarian.yaml` |
| Bot 8 | Tail Risk Combo | `bot_08_tail_risk_combo.py` | `bot_08_tail_risk.yaml` |
| Bot 9 | Advanced Kelly | `bot_09_advanced_kelly.py` + `bot_09_kelly_value.py` | `bot_09_advanced_kelly.yaml` |
| Bot 10 | Long-term Value | `bot_10_longterm.py` + `bot_10_longterm_value.py` | `bot_10_longterm.yaml` |

## Comparison with Old Documentation

| Bot # | OLD Name (contexto_proyecto.md) | **REAL Name** | Match? |
|-------|--------------------------------|---------------|--------|
| Bot 1 | `bot_01_mean_reversion.py` | `bot_01_rebalancer.py` | NO |
| Bot 2 | `bot_02_volatility_breakout.py` | `bot_02_esports.py` | NO |
| Bot 3 | `bot_03_copy_trading.py` | `bot_03_copy_trading.py` | YES |
| Bot 4 | `bot_04_news_driven.py` | `bot_04_news_driven.py` | YES |
| Bot 5 | `bot_05_market_making.py` | `bot_05_market_making.py` | YES |
| Bot 6 | `bot_06_multi_outcome.py` | `bot_06_multi_outcome.py` | YES |
| Bot 7 | `bot_07_contrarian.py` | `bot_07_contrarian.py` | YES |
| Bot 8 | `bot_08_tail_risk.py` | `bot_08_tail_risk_combo.py` | PARTIAL |
| Bot 9 | `bot_09_advanced_kelly.py` | `bot_09_advanced_kelly.py` | YES |
| Bot 10 | `bot_10_longterm_value.py` | `bot_10_longterm.py` | PARTIAL |

## Complete File Listing in src/bots/

```
src/bots/
├── __init__.py
├── base_bot.py                    # Base class for all bots
├── bot_factory.py                 # Bot orchestration (IMPLEMENTED - ~240 lines)
├── bot_01_rebalancer.py
├── bot_01_market_rebalancing.py
├── bot_02_esports.py
├── bot_02_esports_parsing.py
├── bot_03_copy_trading.py
├── bot_04_news_driven.py
├── bot_04_news_scalping.py
├── bot_05_market_making.py
├── bot_06_multi_outcome.py
├── bot_06_multi_outcome_arb.py
├── bot_07_contrarian.py
├── bot_07_contrarian_attention.py
├── bot_08_tail_risk_combo.py      # PRIORITY BOT - fully implemented
├── bot_09_advanced_kelly.py
├── bot_09_kelly_value.py
├── bot_10_longterm.py
└── bot_10_longterm_value.py
```

## Key Findings

1. **10 bots have completely different strategy names between context and code**
   - Documentation mentioned files that DO NOT EXIST (bot_01_mean_reversion.py, etc.)

2. **Documentation claimed "10 Bots implemented (100%)" - but with different names**
   - Some bot references pointed to files that DO NOT EXIST

3. **This mapping is now the AUTHORITATIVE source**
   - All future documentation should reference THIS document

## Resolution Status

- [x] C1-02: Bot files documented vs actual (RESOLVED by this document)
- [x] C1-03: Configuration file mapping (RESOLVED by this document)
- [x] C5-01: Strategy name discrepancies (RESOLVED by this document)
- [x] C5-02: File existence verification (RESOLVED by this document)
