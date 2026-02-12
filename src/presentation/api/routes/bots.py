"""Bot routes."""

import logging
from decimal import Decimal

from fastapi import APIRouter, HTTPException

from src.presentation.api.dependencies import TimescaleDB
from src.presentation.api.schemas.bot import BotCreate, BotResponse, BotStateUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=BotResponse, status_code=201)
async def create_bot(
    bot: BotCreate,
    db: TimescaleDB,
):
    """Create a new bot.

    Args:
        bot: Bot creation data
        db: TimescaleDB client

    Returns:
        Created bot
    """
    logger.info(
        "Creating bot",
        extra={
            "strategy_type": bot.strategy_type,
            "capital": float(bot.capital_allocated),
        },
    )

    # Create bot (simplified - real implementation uses BotRepository)
    query = """
        INSERT INTO bots (strategy_type, state, config, capital_allocated)
        VALUES ($1, $2, $3, $4)
        RETURNING bot_id, strategy_type, state, config, capital_allocated, created_at, updated_at
    """

    import json

    from datetime import datetime

    row = await db.pool.fetchrow(
        query,
        bot.strategy_type,
        "IDLE",
        json.dumps(bot.config),
        bot.capital_allocated,
    )

    return BotResponse(
        bot_id=row["bot_id"],
        strategy_type=row["strategy_type"],
        state=row["state"],
        config=json.loads(row["config"]),
        capital_allocated=row["capital_allocated"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("", response_model=list[BotResponse])
async def list_bots(
    db: TimescaleDB,
    limit: int = 100,
):
    """List all bots.

    Args:
        db: TimescaleDB client
        limit: Maximum number of bots to return

    Returns:
        List of bots
    """
    query = """
        SELECT bot_id, strategy_type, state, config, capital_allocated, created_at, updated_at
        FROM bots
        ORDER BY created_at DESC
        LIMIT $1
    """

    import json

    rows = await db.pool.fetch(query, limit)

    return [
        BotResponse(
            bot_id=row["bot_id"],
            strategy_type=row["strategy_type"],
            state=row["state"],
            config=json.loads(row["config"]),
            capital_allocated=row["capital_allocated"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: int,
    db: TimescaleDB,
):
    """Get bot by ID.

    Args:
        bot_id: Bot ID
        db: TimescaleDB client

    Returns:
        Bot details
    """
    query = """
        SELECT bot_id, strategy_type, state, config, capital_allocated, created_at, updated_at
        FROM bots
        WHERE bot_id = $1
    """

    import json

    row = await db.pool.fetchrow(query, bot_id)

    if not row:
        raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found")

    return BotResponse(
        bot_id=row["bot_id"],
        strategy_type=row["strategy_type"],
        state=row["state"],
        config=json.loads(row["config"]),
        capital_allocated=row["capital_allocated"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.put("/{bot_id}/state", response_model=BotResponse)
async def update_bot_state(
    bot_id: int,
    state_update: BotStateUpdate,
    db: TimescaleDB,
):
    """Update bot state.

    Args:
        bot_id: Bot ID
        state_update: New state
        db: TimescaleDB client

    Returns:
        Updated bot
    """
    logger.info(
        "Updating bot state",
        extra={"bot_id": bot_id, "new_state": state_update.state},
    )

    query = """
        UPDATE bots
        SET state = $1, updated_at = NOW()
        WHERE bot_id = $2
        RETURNING bot_id, strategy_type, state, config, capital_allocated, created_at, updated_at
    """

    import json

    row = await db.pool.fetchrow(query, state_update.state, bot_id)

    if not row:
        raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found")

    return BotResponse(
        bot_id=row["bot_id"],
        strategy_type=row["strategy_type"],
        state=row["state"],
        config=json.loads(row["config"]),
        capital_allocated=row["capital_allocated"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.delete("/{bot_id}", status_code=204)
async def delete_bot(
    bot_id: int,
    db: TimescaleDB,
):
    """Delete bot.

    Args:
        bot_id: Bot ID
        db: TimescaleDB client
    """
    logger.info("Deleting bot", extra={"bot_id": bot_id})

    query = "DELETE FROM bots WHERE bot_id = $1"
    result = await db.pool.execute(query, bot_id)

    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found")

    return None
