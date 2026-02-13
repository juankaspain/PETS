#!/usr/bin/env python3
"""Bot 8 Paper Trading Validation Script.

Execute 30-day paper trading validation for Bot 8 Tail Risk strategy.
Monitors performance against targets: win rate >52%, Sharpe >0.8, drawdown <15%.

Usage:
    python scripts/run_bot8_paper_trading.py

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, Optional

import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.application.use_cases.paper_trading.run_paper_trading import RunPaperTradingUseCase
from src.application.use_cases.paper_trading.get_paper_stats import GetPaperTradingStatsUseCase
from src.infrastructure.paper_trading.paper_trading_engine import PaperTradingEngine
from src.bots.bot_08_tail_risk import TailRiskStrategy
from src.domain.value_objects import BotState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot8_paper_trading.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class Bot8PaperTradingRunner:
    """Bot 8 Paper Trading validation runner.
    
    Executes 30-day paper trading session with real-time monitoring
    and performance tracking against validation targets.
    
    Attributes:
        config: Bot 8 configuration loaded from YAML
        engine: Paper trading engine instance
        bot_strategy: Bot 8 Tail Risk strategy instance
        session_duration_days: 30 days validation period
        validation_targets: Performance targets dict
        metrics: Real-time metrics tracking
        shutdown_requested: Graceful shutdown flag
    """

    def __init__(self) -> None:
        """Initialize Bot 8 paper trading runner."""
        self.config = self._load_bot8_config()
        self.engine = PaperTradingEngine(
            initial_balance=Decimal("5000"),
            config=self.config
        )
        self.bot_strategy = TailRiskStrategy(config=self.config)
        
        # Session configuration
        self.session_duration_days = 30
        self.session_start: Optional[datetime] = None
        self.session_end: Optional[datetime] = None
        
        # Validation targets
        self.validation_targets = {
            "win_rate_pct": Decimal("52.0"),
            "sharpe_ratio": Decimal("0.8"),
            "max_drawdown_pct": Decimal("15.0"),
            "min_trades": 50
        }
        
        # Metrics tracking
        self.metrics: Dict = {
            "trades_count": 0,
            "wins": 0,
            "losses": 0,
            "total_pnl": Decimal("0"),
            "peak_balance": Decimal("5000"),
            "current_drawdown_pct": Decimal("0"),
            "max_drawdown_pct": Decimal("0"),
            "daily_pnls": [],
            "sharpe_ratio": Decimal("0")
        }
        
        # Shutdown handling
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        
        logger.info(
            "bot8_paper_trading_initialized",
            extra={
                "bot_id": "bot_8",
                "strategy": "tail_risk",
                "initial_balance": "5000",
                "session_duration_days": self.session_duration_days,
                "validation_targets": {k: float(v) if isinstance(v, Decimal) else v 
                                     for k, v in self.validation_targets.items()}
            }
        )

    def _load_bot8_config(self) -> Dict:
        """Load Bot 8 configuration from YAML.
        
        Returns:
            Dict with Bot 8 configuration
            
        Raises:
            FileNotFoundError: If config file missing
            yaml.YAMLError: If config invalid
        """
        config_path = Path(__file__).parent.parent / "configs" / "bots" / "bot_8_config.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Bot 8 config not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info("bot8_config_loaded", extra={"config_path": str(config_path)})
        return config

    def _handle_shutdown(self, signum: int, frame) -> None:
        """Handle graceful shutdown on SIGINT/SIGTERM.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.warning("shutdown_requested", extra={"signal": signum})
        self.shutdown_requested = True

    async def run_session(self) -> None:
        """Execute 30-day paper trading validation session.
        
        Main execution loop:
        1. Initialize session
        2. Run daily trading cycles
        3. Collect metrics
        4. Generate daily reports
        5. Check validation targets
        6. Final analysis
        
        Raises:
            Exception: If session execution fails
        """
        try:
            # Session initialization
            self.session_start = datetime.utcnow()
            self.session_end = self.session_start + timedelta(days=self.session_duration_days)
            
            logger.info(
                "session_started",
                extra={
                    "session_start": self.session_start.isoformat(),
                    "session_end": self.session_end.isoformat(),
                    "duration_days": self.session_duration_days
                }
            )
            
            # Initialize bot strategy
            await self.bot_strategy.initialize()
            
            # Main trading loop (simulated days)
            current_day = 0
            while current_day < self.session_duration_days and not self.shutdown_requested:
                day_start = datetime.utcnow()
                
                logger.info(
                    "day_started",
                    extra={
                        "day": current_day + 1,
                        "total_days": self.session_duration_days,
                        "current_balance": float(self.engine.get_balance())
                    }
                )
                
                # Execute trading day (multiple cycles)
                day_metrics = await self._execute_trading_day()
                
                # Update session metrics
                self._update_session_metrics(day_metrics)
                
                # Generate daily report
                self._generate_daily_report(current_day + 1, day_metrics)
                
                # Check if targets met early (optional early stop)
                if current_day >= 7:  # At least 7 days
                    if self._check_early_success():
                        logger.info("early_success_detected", extra={"day": current_day + 1})
                        break
                
                current_day += 1
                
                # Progress update
                progress_pct = (current_day / self.session_duration_days) * 100
                logger.info(
                    "session_progress",
                    extra={
                        "day": current_day,
                        "progress_pct": round(progress_pct, 1),
                        "trades_count": self.metrics["trades_count"],
                        "current_pnl": float(self.metrics["total_pnl"]),
                        "win_rate_pct": self._calculate_win_rate()
                    }
                )
            
            # Session completed
            await self._finalize_session()
            
        except Exception as e:
            logger.error(
                "session_error",
                extra={"error": str(e)},
                exc_info=True
            )
            raise

    async def _execute_trading_day(self) -> Dict:
        """Execute one trading day (multiple cycles).
        
        Returns:
            Dict with day metrics: trades, pnl, signals
        """
        day_metrics = {
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "pnl": Decimal("0"),
            "signals_generated": 0,
            "orders_placed": 0
        }
        
        # Simulate multiple trading cycles per day (e.g., 24 hourly cycles)
        cycles_per_day = 24
        
        for cycle in range(cycles_per_day):
            if self.shutdown_requested:
                break
            
            try:
                # Execute bot strategy cycle
                await self.bot_strategy.execute_cycle()
                
                # Simulate market data updates
                # TODO: Replace with real market data service when available
                await self._simulate_market_update()
                
                # Check for filled orders
                filled_orders = await self._check_filled_orders()
                
                # Update day metrics
                day_metrics["orders_placed"] += len(filled_orders)
                
                # Small delay between cycles (simulate real-time)
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.warning(
                    "cycle_error",
                    extra={"cycle": cycle, "error": str(e)}
                )
                continue
        
        return day_metrics

    async def _simulate_market_update(self) -> None:
        """Simulate market data update.
        
        TODO: Replace with real WebSocket market data when available.
        """
        # Placeholder for market data simulation
        pass

    async def _check_filled_orders(self) -> list:
        """Check for filled virtual orders.
        
        Returns:
            List of filled orders
        """
        # Placeholder - engine handles fills internally
        return []

    def _update_session_metrics(self, day_metrics: Dict) -> None:
        """Update session-wide metrics with day results.
        
        Args:
            day_metrics: Metrics from completed trading day
        """
        # Update trade counts
        self.metrics["trades_count"] += day_metrics["trades"]
        self.metrics["wins"] += day_metrics["wins"]
        self.metrics["losses"] += day_metrics["losses"]
        
        # Update P&L
        self.metrics["total_pnl"] += day_metrics["pnl"]
        self.metrics["daily_pnls"].append(float(day_metrics["pnl"]))
        
        # Update drawdown
        current_balance = self.engine.get_balance()
        if current_balance > self.metrics["peak_balance"]:
            self.metrics["peak_balance"] = current_balance
        
        drawdown = (self.metrics["peak_balance"] - current_balance) / self.metrics["peak_balance"] * 100
        self.metrics["current_drawdown_pct"] = drawdown
        
        if drawdown > self.metrics["max_drawdown_pct"]:
            self.metrics["max_drawdown_pct"] = drawdown
        
        # Update Sharpe ratio (if enough data)
        if len(self.metrics["daily_pnls"]) >= 7:
            self.metrics["sharpe_ratio"] = self._calculate_sharpe_ratio()

    def _calculate_win_rate(self) -> float:
        """Calculate current win rate percentage.
        
        Returns:
            Win rate as percentage (0-100)
        """
        if self.metrics["trades_count"] == 0:
            return 0.0
        
        return (self.metrics["wins"] / self.metrics["trades_count"]) * 100

    def _calculate_sharpe_ratio(self) -> Decimal:
        """Calculate Sharpe ratio from daily P&Ls.
        
        Returns:
            Sharpe ratio (annualized)
        """
        import numpy as np
        
        if len(self.metrics["daily_pnls"]) < 2:
            return Decimal("0")
        
        daily_pnls = np.array(self.metrics["daily_pnls"])
        
        # Calculate mean and std of daily returns
        mean_return = np.mean(daily_pnls)
        std_return = np.std(daily_pnls)
        
        if std_return == 0:
            return Decimal("0")
        
        # Sharpe = (mean_return / std_return) * sqrt(252)  # Annualized
        sharpe = (mean_return / std_return) * np.sqrt(252)
        
        return Decimal(str(round(sharpe, 2)))

    def _generate_daily_report(self, day: int, day_metrics: Dict) -> None:
        """Generate and log daily performance report.
        
        Args:
            day: Day number (1-30)
            day_metrics: Metrics from the day
        """
        report = {
            "day": day,
            "date": datetime.utcnow().isoformat(),
            "balance": float(self.engine.get_balance()),
            "day_pnl": float(day_metrics["pnl"]),
            "total_pnl": float(self.metrics["total_pnl"]),
            "trades_count": self.metrics["trades_count"],
            "win_rate_pct": round(self._calculate_win_rate(), 2),
            "sharpe_ratio": float(self.metrics["sharpe_ratio"]),
            "max_drawdown_pct": float(self.metrics["max_drawdown_pct"]),
            "current_drawdown_pct": float(self.metrics["current_drawdown_pct"])
        }
        
        logger.info("daily_report", extra=report)
        
        # Save to JSON file
        reports_dir = Path("logs/paper_trading_reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = reports_dir / f"bot8_day_{day:02d}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

    def _check_early_success(self) -> bool:
        """Check if validation targets met early.
        
        Returns:
            True if all targets met and can stop early
        """
        if self.metrics["trades_count"] < self.validation_targets["min_trades"]:
            return False
        
        win_rate = Decimal(str(self._calculate_win_rate()))
        
        targets_met = (
            win_rate >= self.validation_targets["win_rate_pct"] and
            self.metrics["sharpe_ratio"] >= self.validation_targets["sharpe_ratio"] and
            self.metrics["max_drawdown_pct"] <= self.validation_targets["max_drawdown_pct"]
        )
        
        return targets_met

    async def _finalize_session(self) -> None:
        """Finalize session with final analysis and report."""
        # Calculate final metrics
        final_balance = self.engine.get_balance()
        roi = ((final_balance - Decimal("5000")) / Decimal("5000")) * 100
        win_rate = Decimal(str(self._calculate_win_rate()))
        
        # Validation results
        validation_passed = (
            self.metrics["trades_count"] >= self.validation_targets["min_trades"] and
            win_rate >= self.validation_targets["win_rate_pct"] and
            self.metrics["sharpe_ratio"] >= self.validation_targets["sharpe_ratio"] and
            self.metrics["max_drawdown_pct"] <= self.validation_targets["max_drawdown_pct"]
        )
        
        # Final report
        final_report = {
            "session_start": self.session_start.isoformat() if self.session_start else None,
            "session_end": datetime.utcnow().isoformat(),
            "duration_days": self.session_duration_days,
            "final_balance": float(final_balance),
            "initial_balance": 5000.0,
            "total_pnl": float(self.metrics["total_pnl"]),
            "roi_pct": float(roi),
            "trades_count": self.metrics["trades_count"],
            "wins": self.metrics["wins"],
            "losses": self.metrics["losses"],
            "win_rate_pct": float(win_rate),
            "sharpe_ratio": float(self.metrics["sharpe_ratio"]),
            "max_drawdown_pct": float(self.metrics["max_drawdown_pct"]),
            "validation": {
                "targets": {
                    "win_rate_pct": float(self.validation_targets["win_rate_pct"]),
                    "sharpe_ratio": float(self.validation_targets["sharpe_ratio"]),
                    "max_drawdown_pct": float(self.validation_targets["max_drawdown_pct"]),
                    "min_trades": self.validation_targets["min_trades"]
                },
                "results": {
                    "win_rate_met": win_rate >= self.validation_targets["win_rate_pct"],
                    "sharpe_met": self.metrics["sharpe_ratio"] >= self.validation_targets["sharpe_ratio"],
                    "drawdown_met": self.metrics["max_drawdown_pct"] <= self.validation_targets["max_drawdown_pct"],
                    "trades_met": self.metrics["trades_count"] >= self.validation_targets["min_trades"]
                },
                "passed": validation_passed
            }
        }
        
        logger.info("session_finalized", extra=final_report)
        
        # Save final report
        reports_dir = Path("logs/paper_trading_reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        final_report_file = reports_dir / "bot8_final_report.json"
        with open(final_report_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        # Print summary to console
        print("\n" + "="*80)
        print("BOT 8 PAPER TRADING VALIDATION - FINAL REPORT")
        print("="*80)
        print(f"Duration: {self.session_duration_days} days")
        print(f"Final Balance: ${float(final_balance):,.2f}")
        print(f"Total P&L: ${float(self.metrics['total_pnl']):,.2f} ({float(roi):+.2f}%)")
        print(f"Trades: {self.metrics['trades_count']} ({self.metrics['wins']}W / {self.metrics['losses']}L)")
        print(f"Win Rate: {float(win_rate):.2f}% (target: >={float(self.validation_targets['win_rate_pct'])}%)")
        print(f"Sharpe Ratio: {float(self.metrics['sharpe_ratio']):.2f} (target: >={float(self.validation_targets['sharpe_ratio'])})")
        print(f"Max Drawdown: {float(self.metrics['max_drawdown_pct']):.2f}% (target: <={float(self.validation_targets['max_drawdown_pct'])}%)")
        print("="*80)
        print(f"VALIDATION: {'✅ PASSED' if validation_passed else '❌ FAILED'}")
        print("="*80)
        
        if validation_passed:
            print("\n🎉 Bot 8 ready for LIVE DEPLOYMENT (Fase 15)")
            print("Next steps:")
            print("  1. Review final report: logs/paper_trading_reports/bot8_final_report.json")
            print("  2. Proceed to Fase 15: Live Trading Deployment")
            print("  3. Setup hot wallet + mainnet configuration")
        else:
            print("\n⚠️  Targets not met - Adjustment required")
            print("Next steps:")
            print("  1. Review daily reports: logs/paper_trading_reports/bot8_day_*.json")
            print("  2. Analyze failure points")
            print("  3. Adjust config: configs/bots/bot_8_config.yaml")
            print("  4. Re-run paper trading validation")
        
        # Graceful bot shutdown
        await self.bot_strategy.stop_gracefully()


async def main() -> None:
    """Main entry point."""
    print("\n" + "="*80)
    print("BOT 8 PAPER TRADING VALIDATION - STARTING")
    print("="*80)
    print("Duration: 30 days simulation")
    print("Initial Balance: $5,000")
    print("Strategy: Tail Risk (Z1-Z2 only)")
    print("Targets: Win rate >52%, Sharpe >0.8, Drawdown <15%")
    print("="*80 + "\n")
    
    runner = Bot8PaperTradingRunner()
    
    try:
        await runner.run_session()
    except KeyboardInterrupt:
        logger.warning("session_interrupted_by_user")
        print("\n⚠️  Session interrupted by user")
    except Exception as e:
        logger.error("session_failed", extra={"error": str(e)}, exc_info=True)
        print(f"\n❌ Session failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
