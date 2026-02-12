"""Paper trade use case for real-time simulation."""

import logging
from decimal import Decimal
from uuid import UUID

from src.application.bots.bot8_volatility_skew import Bot8VolatilitySkew
from src.domain.entities.market import Market
from src.domain.value_objects.price import Price
from src.infrastructure.paper_trading.paper_wallet import PaperWallet
from src.infrastructure.paper_trading.simulated_execution import SimulatedExecution

logger = logging.getLogger(__name__)


class PaperTradeUseCase:
    """Use case for paper trading in real-time."""

    def __init__(
        self,
        paper_wallet: PaperWallet,
        execution_engine: SimulatedExecution,
        strategy: Bot8VolatilitySkew,
    ):
        """Initialize use case.

        Args:
            paper_wallet: Paper wallet instance
            execution_engine: Simulated execution engine
            strategy: Trading strategy
        """
        self.paper_wallet = paper_wallet
        self.execution_engine = execution_engine
        self.strategy = strategy

    async def analyze_and_trade(
        self,
        market: Market,
        yes_price: Price,
        no_price: Price,
    ) -> UUID | None:
        """Analyze market and place paper trade if signal is positive.

        Args:
            market: Market entity
            yes_price: Current YES price
            no_price: Current NO price

        Returns:
            Order ID if trade placed, None otherwise
        """
        logger.debug(
            "Analyzing market for paper trading",
            extra={
                "market_id": market.market_id,
                "yes_price": float(yes_price.value),
            },
        )

        # Analyze market
        signal = self.strategy.analyze_market(market, yes_price, no_price)

        if not signal["should_enter"]:
            return None

        # Calculate position size
        portfolio_value = self.paper_wallet.get_total_value(
            {market.market_id: yes_price.value}
        )

        position_size = self.strategy.calculate_position_size(
            market=market,
            entry_price=signal["entry_price"],
            portfolio_value=portfolio_value,
        )

        if position_size <= 0:
            logger.info("Position size too small, skipping trade")
            return None

        # Submit order
        try:
            order_id = self.execution_engine.submit_order(
                market_id=market.market_id,
                side=signal["side"],
                size=position_size,
                price=signal["entry_price"].value,
                post_only=True,
            )

            logger.info(
                "Paper trade order submitted",
                extra={
                    "order_id": str(order_id),
                    "market_id": market.market_id,
                    "side": signal["side"],
                    "size": float(position_size),
                    "price": float(signal["entry_price"].value),
                },
            )

            return order_id

        except ValueError as e:
            logger.warning(f"Failed to submit paper trade: {e}")
            return None

    async def process_market_update(
        self,
        market_id: str,
        current_price: Price,
    ) -> None:
        """Process market price update.

        Args:
            market_id: Market ID
            current_price: Current price
        """
        # Fill matching orders
        filled_orders = self.execution_engine.process_market_update(
            market_id=market_id,
            current_price=current_price.value,
        )

        if filled_orders:
            logger.info(
                "Orders filled in paper trading",
                extra={
                    "market_id": market_id,
                    "filled_count": len(filled_orders),
                },
            )
