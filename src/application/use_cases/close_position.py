"""Close position use case."""

import logging
from decimal import Decimal
from uuid import UUID

from src.domain.protocols.repositories import PositionRepository
from src.domain.services.pnl_calculator import PnLCalculator
from src.domain.value_objects.price import Price

logger = logging.getLogger(__name__)


class ClosePositionUseCase:
    """Close position use case.

    Workflow:
    1. Get position from repository
    2. Calculate final P&L
    3. Update position (close)
    4. Record metrics
    5. Emit position_closed event

    Example:
        >>> use_case = ClosePositionUseCase(position_repo, pnl_calc)
        >>> await use_case.execute(
        ...     position_id=position_id,
        ...     exit_price=Decimal("0.60"),
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
        position_id: UUID,
        exit_price: Decimal,
    ) -> Decimal:
        """Execute close position use case.

        Args:
            position_id: Position ID
            exit_price: Exit price

        Returns:
            Realized P&L

        Raises:
            ValueError: If position not found or already closed
        """
        logger.info(
            "Closing position",
            extra={
                "position_id": str(position_id),
                "exit_price": float(exit_price),
            },
        )

        # 1. Get position
        position_data = await self.position_repo.get_by_id(position_id)
        if not position_data:
            raise ValueError(f"Position {position_id} not found")

        if position_data.get("closed_at"):
            raise ValueError(f"Position {position_id} already closed")

        # 2. Calculate final P&L
        from src.domain.entities.order import OrderSide

        entry_price = Decimal(str(position_data["entry_price"]))
        size = Decimal(str(position_data["size"]))
        side = position_data["side"]

        if side == OrderSide.BUY.value:
            pnl = (exit_price - entry_price) * size
        else:
            pnl = (entry_price - exit_price) * size

        logger.info(
            "P&L calculated",
            extra={
                "position_id": str(position_id),
                "entry_price": float(entry_price),
                "exit_price": float(exit_price),
                "size": float(size),
                "pnl": float(pnl),
            },
        )

        # 3. Close position
        await self.position_repo.close(
            position_id=position_id,
            realized_pnl=pnl,
        )

        logger.info(
            "Position closed",
            extra={
                "position_id": str(position_id),
                "realized_pnl": float(pnl),
            },
        )

        # 4. Emit event (handled by infrastructure)

        return pnl
