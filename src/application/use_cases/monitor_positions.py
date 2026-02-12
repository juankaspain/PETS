"""Monitor positions use case."""

import logging
from decimal import Decimal
from typing import Optional

from src.domain.protocols.repositories import PositionRepository
from src.domain.services.pnl_calculator import PnLCalculator

logger = logging.getLogger(__name__)


class MonitorPositionsUseCase:
    """Monitor positions use case.

    Workflow:
    1. Get all open positions for bot
    2. Calculate current P&L for each
    3. Check exit conditions
    4. Emit alerts if needed

    Example:
        >>> use_case = MonitorPositionsUseCase(position_repo, pnl_calc)
        >>> signals = await use_case.execute(
        ...     bot_id=1,
        ...     current_prices={"0x123...": Decimal("0.60")},
        ... )
    """

    def __init__(
        self,
        position_repository: PositionRepository,
        pnl_calculator: PnLCalculator,
    ) -> None:
        """Initialize use case.

        Args:
            position_repository: Position repository
            pnl_calculator: P&L calculator
        """
        self.position_repo = position_repository
        self.pnl_calc = pnl_calculator

    async def execute(
        self,
        bot_id: int,
        current_prices: dict[str, Decimal],
    ) -> list[dict]:
        """Execute monitor positions use case.

        Args:
            bot_id: Bot ID to monitor
            current_prices: Dict of market_id -> current_price

        Returns:
            List of position signals (exit recommendations)
        """
        # 1. Get open positions
        positions = await self.position_repo.get_open(bot_id=bot_id)

        logger.debug(
            "Monitoring positions",
            extra={"bot_id": bot_id, "position_count": len(positions)},
        )

        signals = []

        for position_data in positions:
            market_id = position_data["market_id"]
            current_price = current_prices.get(market_id)

            if not current_price:
                continue

            # 2. Calculate P&L
            from src.domain.entities.order import OrderSide

            entry_price = Decimal(str(position_data["entry_price"]))
            size = Decimal(str(position_data["size"]))
            side = position_data["side"]

            if side == OrderSide.BUY.value:
                pnl = (current_price - entry_price) * size
            else:
                pnl = (entry_price - current_price) * size

            pnl_pct = pnl / (size * entry_price) if size * entry_price > 0 else Decimal("0")

            # 3. Update unrealized P&L
            await self.position_repo.update_pnl(
                position_id=position_data["position_id"],
                current_price=current_price,
                unrealized=pnl,
            )

            # 4. Check exit conditions
            # (Simplified - full logic in bot strategy)
            if pnl_pct > Decimal("0.25"):  # 25% profit
                signals.append(
                    {
                        "position_id": position_data["position_id"],
                        "action": "exit",
                        "reason": "target_profit",
                        "pnl_pct": float(pnl_pct),
                    }
                )
            elif pnl_pct < Decimal("-0.10"):  # 10% loss
                signals.append(
                    {
                        "position_id": position_data["position_id"],
                        "action": "exit",
                        "reason": "stop_loss",
                        "pnl_pct": float(pnl_pct),
                    }
                )

        if signals:
            logger.info(
                "Exit signals generated",
                extra={"bot_id": bot_id, "signal_count": len(signals)},
            )

        return signals
