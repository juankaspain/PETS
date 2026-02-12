"""Market routes."""

import logging
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query

from src.presentation.api.dependencies import TimescaleDB
from src.presentation.api.schemas.market import MarketResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[MarketResponse])
async def list_markets(
    db: TimescaleDB,
    active: bool = Query(True, description="Filter active markets only"),
    min_liquidity: Decimal | None = Query(
        None, description="Minimum liquidity filter"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
):
    """List markets.

    Args:
        db: TimescaleDB client
        active: Filter active markets
        min_liquidity: Minimum liquidity
        limit: Maximum results

    Returns:
        List of markets
    """
    # Build query
    conditions = []
    params = []
    param_count = 1

    if active:
        conditions.append("resolved = FALSE")

    if min_liquidity is not None:
        conditions.append(f"liquidity >= ${param_count}")
        params.append(min_liquidity)
        param_count += 1

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
        SELECT market_id, question, outcomes, liquidity, volume_24h, yes_price, no_price,
               created_at, updated_at, resolves_at, resolved, resolved_outcome
        FROM markets
        {where_clause}
        ORDER BY liquidity DESC
        LIMIT ${param_count}
    """
    params.append(limit)

    rows = await db.pool.fetch(query, *params)

    return [
        MarketResponse(
            market_id=row["market_id"],
            question=row["question"],
            outcomes=row["outcomes"],
            liquidity=row["liquidity"],
            volume_24h=row["volume_24h"],
            yes_price=row["yes_price"],
            no_price=row["no_price"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            resolves_at=row["resolves_at"],
            resolved=row["resolved"],
            resolved_outcome=row["resolved_outcome"],
        )
        for row in rows
    ]


@router.get("/{market_id}", response_model=MarketResponse)
async def get_market(
    market_id: str,
    db: TimescaleDB,
):
    """Get market by ID.

    Args:
        market_id: Market ID
        db: TimescaleDB client

    Returns:
        Market details
    """
    query = """
        SELECT market_id, question, outcomes, liquidity, volume_24h, yes_price, no_price,
               created_at, updated_at, resolves_at, resolved, resolved_outcome
        FROM markets
        WHERE market_id = $1
    """

    row = await db.pool.fetchrow(query, market_id)

    if not row:
        raise HTTPException(status_code=404, detail=f"Market {market_id} not found")

    return MarketResponse(
        market_id=row["market_id"],
        question=row["question"],
        outcomes=row["outcomes"],
        liquidity=row["liquidity"],
        volume_24h=row["volume_24h"],
        yes_price=row["yes_price"],
        no_price=row["no_price"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        resolves_at=row["resolves_at"],
        resolved=row["resolved"],
        resolved_outcome=row["resolved_outcome"],
    )
