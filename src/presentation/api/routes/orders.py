"""Order routes."""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from src.application.use_cases.place_order import PlaceOrderUseCase
from src.infrastructure.repositories.order_repository import OrderRepository
from src.presentation.api.dependencies import RiskCalc, TimescaleDB
from src.presentation.api.schemas.order import OrderCancel, OrderCreate, OrderResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=dict, status_code=201)
async def place_order(
    order: OrderCreate,
    db: TimescaleDB,
    risk_calc: RiskCalc,
):
    """Place a new order.

    Args:
        order: Order data
        db: TimescaleDB client
        risk_calc: Risk calculator

    Returns:
        Order ID
    """
    logger.info(
        "Placing order",
        extra={
            "bot_id": order.bot_id,
            "market_id": order.market_id,
            "side": order.side,
            "size": float(order.size),
            "price": float(order.price),
        },
    )

    # Create repository and use case
    order_repo = OrderRepository(db, None)  # Redis not needed for this example
    use_case = PlaceOrderUseCase(order_repo, risk_calc)

    # Execute use case
    order_id = await use_case.execute(
        bot_id=order.bot_id,
        market_id=order.market_id,
        side=order.side,
        size=order.size,
        price=order.price,
        zone=order.zone,
        portfolio_value=10000,  # TODO: Get from wallet
        post_only=order.post_only,
    )

    return {"order_id": str(order_id)}


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    db: TimescaleDB,
    bot_id: int | None = Query(None, description="Filter by bot ID"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
):
    """List orders.

    Args:
        db: TimescaleDB client
        bot_id: Filter by bot ID
        status: Filter by status
        limit: Maximum results

    Returns:
        List of orders
    """
    # Build query
    conditions = []
    params = []
    param_count = 1

    if bot_id is not None:
        conditions.append(f"bot_id = ${param_count}")
        params.append(bot_id)
        param_count += 1

    if status is not None:
        conditions.append(f"status = ${param_count}")
        params.append(status)
        param_count += 1

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
        SELECT order_id, bot_id, market_id, side, size, price, zone, status, post_only,
               created_at, updated_at, filled_size
        FROM orders
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ${param_count}
    """
    params.append(limit)

    rows = await db.pool.fetch(query, *params)

    return [
        OrderResponse(
            order_id=row["order_id"],
            bot_id=row["bot_id"],
            market_id=row["market_id"],
            side=row["side"],
            size=row["size"],
            price=row["price"],
            zone=row["zone"],
            status=row["status"],
            post_only=row["post_only"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            filled_size=row["filled_size"],
        )
        for row in rows
    ]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    db: TimescaleDB,
):
    """Get order by ID.

    Args:
        order_id: Order ID
        db: TimescaleDB client

    Returns:
        Order details
    """
    query = """
        SELECT order_id, bot_id, market_id, side, size, price, zone, status, post_only,
               created_at, updated_at, filled_size
        FROM orders
        WHERE order_id = $1
    """

    row = await db.pool.fetchrow(query, order_id)

    if not row:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

    return OrderResponse(
        order_id=row["order_id"],
        bot_id=row["bot_id"],
        market_id=row["market_id"],
        side=row["side"],
        size=row["size"],
        price=row["price"],
        zone=row["zone"],
        status=row["status"],
        post_only=row["post_only"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        filled_size=row["filled_size"],
    )


@router.put("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: UUID,
    cancel_data: OrderCancel,
    db: TimescaleDB,
):
    """Cancel order.

    Args:
        order_id: Order ID
        cancel_data: Cancel data
        db: TimescaleDB client

    Returns:
        Cancelled order
    """
    logger.info(
        "Cancelling order",
        extra={"order_id": str(order_id), "reason": cancel_data.reason},
    )

    query = """
        UPDATE orders
        SET status = 'CANCELLED', updated_at = NOW()
        WHERE order_id = $1 AND status IN ('PENDING', 'SUBMITTED', 'OPEN', 'PARTIALLY_FILLED')
        RETURNING order_id, bot_id, market_id, side, size, price, zone, status, post_only,
                  created_at, updated_at, filled_size
    """

    row = await db.pool.fetchrow(query, order_id)

    if not row:
        raise HTTPException(
            status_code=400,
            detail=f"Order {order_id} not found or cannot be cancelled",
        )

    return OrderResponse(
        order_id=row["order_id"],
        bot_id=row["bot_id"],
        market_id=row["market_id"],
        side=row["side"],
        size=row["size"],
        price=row["price"],
        zone=row["zone"],
        status=row["status"],
        post_only=row["post_only"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        filled_size=row["filled_size"],
    )
