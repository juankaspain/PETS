"""Automated paper trading bot."""

import asyncio
import logging
from decimal import Decimal

from src.application.bots.bot8_volatility_skew import Bot8VolatilitySkew
from src.application.paper_trading.paper_wallet_service import PaperWalletService
from src.application.paper_trading.simulated_execution import SimulatedExecution
from src.domain.entities.paper_wallet import PaperWallet
from src.domain.services.risk_calculator import RiskCalculator
from src.infrastructure.repositories.paper_wallet_repository import (
    PaperWalletRepository,
)

logger = logging.getLogger(__name__)


class AutoPaperBot:
    """Automated paper trading bot.
    
    Runs Bot 8 strategy in paper trading mode:
    - Monitors markets via WebSocket
    - Generates Bot 8 signals
    - Executes paper trades automatically
    - Respects circuit breakers
    - Logs all signals and executions
    
    Zero risk - all trades simulated.
    """

    def __init__(
        self,
        wallet_repo: PaperWalletRepository,
        wallet_service: PaperWalletService,
        risk_calculator: RiskCalculator,
    ):
        """Initialize auto paper bot.
        
        Args:
            wallet_repo: Paper wallet repository
            wallet_service: Paper wallet service
            risk_calculator: Risk calculator
        """
        self.wallet_repo = wallet_repo
        self.wallet_service = wallet_service
        self.risk_calculator = risk_calculator
        self.execution = SimulatedExecution()
        self.bot8 = Bot8VolatilitySkew()
        self.running = False
        self.positions = {}  # market_id -> position

    async def start(self):
        """Start automated paper trading."""
        logger.info("Starting automated paper trading")
        self.running = True
        
        # Get or create wallet
        wallet = await self.wallet_repo.get_wallet()
        if not wallet:
            wallet = self.wallet_service.create_wallet()
            await self.wallet_repo.save_wallet(wallet)
        
        # Main loop
        while self.running:
            try:
                await self.trading_loop(wallet)
                await asyncio.sleep(10)  # Check every 10s
            except Exception as e:
                logger.error(f"Auto paper bot error: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def stop(self):
        """Stop automated paper trading."""
        logger.info("Stopping automated paper trading")
        self.running = False

    async def trading_loop(self, wallet: PaperWallet):
        """Main trading loop.
        
        Args:
            wallet: Paper wallet
        """
        # 1. Check circuit breakers
        if self.should_stop_trading(wallet):
            logger.warning("Circuit breakers triggered, stopping trading")
            return
        
        # 2. Get open positions
        positions = await self.wallet_repo.get_positions(status="open")
        
        # 3. Check exit signals for open positions
        for position in positions:
            should_exit, reason = self.bot8.should_exit(
                entry_price=float(position.entry_price),
                current_price=float(position.current_price) if position.current_price else float(position.entry_price),
                hours_held=24,  # TODO: Calculate actual hours
                side=position.side,
            )
            
            if should_exit:
                logger.info(
                    f"Exit signal: {position.market_id}",
                    extra={"reason": reason},
                )
                await self.close_paper_position(wallet, position, reason)
        
        # 4. Scan for new entry signals
        # TODO: Fetch active markets from API
        # For now, this is a placeholder
        # In production, would scan all markets via WebSocket
        
        logger.debug("Trading loop iteration complete")

    def should_stop_trading(self, wallet: PaperWallet) -> bool:
        """Check if should stop trading (circuit breakers).
        
        Args:
            wallet: Paper wallet
            
        Returns:
            True if should stop trading
        """
        # Check drawdown
        total_return_pct = wallet.total_return_pct
        
        if total_return_pct < -25:  # 25% drawdown
            logger.error(
                "Bot drawdown exceeded 25%",
                extra={"drawdown": float(total_return_pct)},
            )
            return True
        
        # Check consecutive losses
        recent_positions = []  # TODO: Get last 3 positions
        consecutive_losses = sum(
            1 for p in recent_positions[-3:]
            if p.realized_pnl and p.realized_pnl < 0
        )
        
        if consecutive_losses >= 3:
            logger.error("3 consecutive losses, circuit breaker triggered")
            return True
        
        return False

    async def close_paper_position(
        self,
        wallet: PaperWallet,
        position,
        reason: str,
    ):
        """Close paper position.
        
        Args:
            wallet: Paper wallet
            position: Position to close
            reason: Close reason
        """
        # Use current price as exit price
        exit_price = position.current_price or position.entry_price
        
        # Close position
        new_wallet, closed_position, exit_trade = self.wallet_service.close_position(
            wallet,
            position,
            exit_price,
        )
        
        # Save to repo
        await self.wallet_repo.save_wallet(new_wallet)
        await self.wallet_repo.save_position(closed_position)
        
        logger.info(
            "Paper position closed",
            extra={
                "position_id": str(position.position_id),
                "reason": reason,
                "realized_pnl": float(closed_position.realized_pnl),
            },
        )

    async def handle_market_update(self, market_data: dict):
        """Handle market price update from WebSocket.
        
        Args:
            market_data: Market update data
        """
        market_id = market_data.get("market")
        yes_price = Decimal(str(market_data.get("yes_price", 0)))
        no_price = Decimal(str(market_data.get("no_price", 0)))
        
        # Update position prices
        positions = await self.wallet_repo.get_positions(status="open")
        
        for position in positions:
            if position.market_id == market_id:
                current_price = yes_price if position.side == "BUY" else no_price
                updated_position = position.update_price(current_price)
                await self.wallet_repo.save_position(updated_position)
        
        # Check for entry signals
        wallet = await self.wallet_repo.get_wallet()
        
        if wallet:
            await self.check_entry_signal(wallet, market_data)

    async def check_entry_signal(
        self,
        wallet: PaperWallet,
        market_data: dict,
    ):
        """Check for Bot 8 entry signal.
        
        Args:
            wallet: Paper wallet
            market_data: Market data
        """
        market_id = market_data.get("market")
        yes_price = float(market_data.get("yes_price", 0.5))
        no_price = float(market_data.get("no_price", 0.5))
        liquidity = float(market_data.get("liquidity", 0))
        
        # Analyze market
        signal = self.bot8.analyze_market(
            market_id=market_id,
            yes_price=yes_price,
            no_price=no_price,
            liquidity=liquidity,
        )
        
        if signal:
            logger.info(
                f"Bot 8 signal: {market_id}",
                extra={"signal": signal},
            )
            
            # TODO: Execute paper trade
            # await self.execute_paper_trade(wallet, signal)
