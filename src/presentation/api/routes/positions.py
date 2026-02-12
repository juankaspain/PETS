"""Position routes."""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from src.presentation.api.dependencies import TimescaleDB
from src.presentation.api.schemas.position import PositionClose, PositionResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[PositionResponse])
async def list_positions(
    db: TimescaleDB,
    bot_id: int | None = Query(None, description="Filter by bot ID"),
    status: str | None = Query(None, description="Filter by status (open/closed)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
):
    """List positions.

    Args:
        db: TimescaleDB client
        bot_id: Filter by bot ID
        status: Filter by status
        limit: Maximum results

    Returns:
        List of positions
    """
    # Build query
    conditions = []
    params = []
    param_count = 1

    if bot_id is not None:
        conditions.append(f"bot_id = ${param_count}")
        params.append(bot_id)
        param_count += 1

    if status == "open":
        conditions.append("closed_at IS NULL")
    elif status == "closed":
        conditions.append("closed_at IS NOT NULL")

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
        SELECT position_id, bot_id, order_id, market_id, side, size, entry_price, zone,
               opened_at, current_price, realized_pnl, unrealized_pnl, closed_at
        FROM positions
        {where_clause}
        ORDER BY opened_at DESC
        LIMIT ${param_count}
    """
    params.append(limit)

    rows = await db.pool.fetch(query, *params)

    return [
        PositionResponse(
            position_id=row["position_id"],
            bot_id=row["bot_id"],
            order_id=row["order_id"],
            market_id=row["market_id"],
            side=row["side"],
            size=row["size"],
            entry_price=row["entry_price"],
            zone=row["zone"],
            opened_at=row["opened_at"],
            current_price=row["current_price"],
            realized_pnl=row["realized_pnl"],
            unrealized_pnl=row["unrealized_pnl"],
            closed_at=row["closed_at"],
        )
        for row in rows
    ]


@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: UUID,
    db: TimescaleDB,
):
    """Get position by ID.

    Args:
        position_id: Position ID
        db: TimescaleDB client

    Returns:
        Position details
    """
    query = """
        SELECT position_id, bot_id, order_id, market_id, side, size, entry_price, zone,
               opened_at, current_price, realized_pnl, unrealized_pnl, closed_at
        FROM positions
        WHERE position_id = $1
    """

    row = await db.pool.fetchrow(query, position_id)

    if not row:
        raise HTTPException(
            status_code=404, detail=f"Position {position_id} not found"
        )

    return PositionResponse(
        position_id=row["position_id"],
        bot_id=row["bot_id"],
        order_id=row["order_id"],
        market_id=row["market_id"],
        side=row["side"],
        size=row["size"],
        entry_price=row["entry_price"],
        zone=row["zone"],
        opened_at=row["opened_at"],
        current_price=row["current_price"],
        realized_pnl=row["realized_pnl"],
        unrealized_pnl=row["unrealized_pnl"],
        closed_at=row["closed_at"],
    )


@router.put("/{position_id}/close", response_model=PositionResponse)
async def close_position(
    position_id: UUID,
    close_data: PositionClose,
    db: TimescaleDB,
):
    """Close position.

    Args:
        position_id: Position ID
        close_data: Close data
        db: TimescaleDB client

    Returns:
        Closed position
    """
    logger.info(
        "Closing position",
        extra={
            "position_id": str(position_id),
            "exit_price": float(close_data.exit_price),
        },
    )

    # Calculate realized P&L (simplified)
    get_query = """
        SELECT entry_price, size, side
        FROM positions
        WHERE position_id = $1 AND closed_at IS NULL
    """

    position = await db.pool.fetchrow(get_query, position_id)

    if not position:
        raise HTTPException(
            status_code=400,
            detail=f"Position {position_id} not found or already closed",
        )

    # Calculate P&L
    entry_price = position["entry_price"]
    size = position["size"]
    side = position["side"]

    if side == "BUY":
        realized_pnl = (close_data.exit_price - entry_price) * size
    else:
        realized_pnl = (entry_price - close_data.exit_price) * size

    # Update position
    update_query = """
        UPDATE positions
        SET realized_pnl = $1, closed_at = NOW(), updated_at = NOW()
        WHERE position_id = $2
        RETURNING position_id, bot_id, order_id, market_id, side, size, entry_price, zone,
                  opened_at, current_price, realized_pnl, unrealized_pnl, closed_at
    """

    row = await db.pool.fetchrow(update_query, realized_pnl, position_id)

    return PositionResponse(
        position_id=row["position_id"],
        bot_id=row["bot_id"],
        order_id=row["order_id"],
        market_id=row["market_id"],
        side=row["side"],
        size=row["size"],
        entry_price=row["entry_price"],
        zone=row["zone"],
        opened_at=row["opened_at"],
        current_price=row["current_price"],
        realized_pnl=row["realized_pnl"],
        unrealized_pnl=row["unrealized_pnl"],
        closed_at=row["closed_at"],
    )
