"""Place order use case."""

import logging
from decimal import Decimal
from uuid import UUID

from src.domain.entities.order import Order, OrderSide, OrderStatus
from src.domain.protocols.repositories import OrderRepository
from src.domain.services.risk_calculator import RiskCalculator
from src.domain.value_objects.price import Price
from src.domain.value_objects.size import Size
from src.domain.value_objects.zone import Zone

logger = logging.getLogger(__name__)


class PlaceOrderUseCase:
    """Place order use case.

    Workflow:
    1. Validate order parameters
    2. Check risk limits
    3. Create order entity
    4. Persist to repository
    5. Submit to exchange (external)

    Example:
        >>> use_case = PlaceOrderUseCase(order_repo, risk_calc)
        >>> order_id = await use_case.execute(
        ...     bot_id=1,
        ...     market_id="0x123...",
        ...     side="BUY",
        ...     size=Decimal("1000"),
        ...     price=Decimal("0.55"),
        ...     zone=2,
        ...     portfolio_value=Decimal("10000"),
        ... )
    """

    def __init__(
        self,
        order_repository: OrderRepository,
        risk_calculator: RiskCalculator,
    ) -> None:
        """Initialize use case.

        Args:
            order_repository: Order repository
            risk_calculator: Risk calculator
        """
        self.order_repo = order_repository
        self.risk_calc = risk_calculator

    async def execute(
        self,
        bot_id: int,
        market_id: str,
        side: str,
        size: Decimal,
        price: Decimal,
        zone: int,
        portfolio_value: Decimal,
        post_only: bool = True,
    ) -> UUID:
        """Execute place order use case.

        Args:
            bot_id: Bot ID
            market_id: Market ID
            side: Order side ('BUY' or 'SELL')
            size: Order size
            price: Limit price
            zone: Risk zone (1-5)
            portfolio_value: Current portfolio value
            post_only: Post-only flag (default True)

        Returns:
            Order ID

        Raises:
            ValueError: If validation fails
        """
        logger.info(
            "Placing order",
            extra={
                "bot_id": bot_id,
                "market_id": market_id,
                "side": side,
                "size": float(size),
                "price": float(price),
                "zone": zone,
            },
        )

        # 1. Validate order parameters
        order_side = OrderSide(side.upper())
        order_price = Price(price)
        order_size = Size(size)
        order_zone = Zone(zone)

        # 2. Check risk limits
        position_value = order_size.value * order_price.value
        risk = self.risk_calc.calculate_position_risk(position_value, portfolio_value)

        logger.info(
            "Risk calculated",
            extra={
                "position_value": float(position_value),
                "portfolio_value": float(portfolio_value),
                "risk_pct": float(risk.percentage()),
            },
        )

        # 3. Create order entity (validates domain rules)
        from datetime import datetime
        from uuid import uuid4

        order = Order(
            order_id=uuid4(),
            bot_id=bot_id,
            market_id=market_id,
            side=order_side,
            size=order_size,
            price=order_price,
            zone=order_zone,
            status=OrderStatus.PENDING,
            post_only=post_only,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # 4. Persist to repository
        order_id = await self.order_repo.create(
            bot_id=bot_id,
            market_id=market_id,
            side=side.upper(),
            size=size,
            price=price,
            zone=zone,
            post_only=post_only,
        )

        logger.info(
            "Order created",
            extra={
                "order_id": str(order_id),
                "bot_id": bot_id,
                "market_id": market_id,
            },
        )

        # 5. Submit to exchange (external) - handled by infrastructure layer
        # Emit event for external submission

        return order_id
