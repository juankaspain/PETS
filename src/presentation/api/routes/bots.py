"""Bot management routes.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from fastapi import APIRouter, Depends, HTTPException, status

from src.presentation.api.dependencies import (
    get_bot_orchestrator,
    get_bot_repository,
)
from src.presentation.api.schemas import (
    BotConfigUpdate,
    BotListResponse,
    BotResponse,
)

router = APIRouter(prefix="/bots", tags=["bots"])


@router.get("", response_model=BotListResponse)
async def list_bots(
    bot_repo=Depends(get_bot_repository),
) -> BotListResponse:
    """List all bots.
    
    Returns:
        List of all bots with their current status
    """
    bots = await bot_repo.find_all()
    return BotListResponse(
        bots=[BotResponse.model_validate(bot) for bot in bots],
        total=len(bots),
    )


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: int,
    bot_repo=Depends(get_bot_repository),
) -> BotResponse:
    """Get bot details.
    
    Args:
        bot_id: Bot identifier
    
    Returns:
        Bot details including metrics
    
    Raises:
        HTTPException: If bot not found
    """
    bot = await bot_repo.find_by_id(bot_id)
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot {bot_id} not found",
        )
    return BotResponse.model_validate(bot)


@router.post("/{bot_id}/start", status_code=status.HTTP_202_ACCEPTED)
async def start_bot(
    bot_id: int,
    orchestrator=Depends(get_bot_orchestrator),
) -> dict[str, str]:
    """Start bot.
    
    Args:
        bot_id: Bot identifier
    
    Returns:
        Status message
    
    Raises:
        HTTPException: If bot not found or cannot start
    """
    try:
        await orchestrator.start_bot(bot_id)
        return {"status": "starting", "bot_id": str(bot_id)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start bot: {str(e)}",
        )


@router.post("/{bot_id}/stop", status_code=status.HTTP_202_ACCEPTED)
async def stop_bot(
    bot_id: int,
    orchestrator=Depends(get_bot_orchestrator),
) -> dict[str, str]:
    """Stop bot.
    
    Args:
        bot_id: Bot identifier
    
    Returns:
        Status message
    
    Raises:
        HTTPException: If bot not found or cannot stop
    """
    try:
        await orchestrator.stop_bot(bot_id)
        return {"status": "stopping", "bot_id": str(bot_id)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop bot: {str(e)}",
        )


@router.post("/{bot_id}/pause", status_code=status.HTTP_202_ACCEPTED)
async def pause_bot(
    bot_id: int,
    orchestrator=Depends(get_bot_orchestrator),
) -> dict[str, str]:
    """Pause bot.
    
    Args:
        bot_id: Bot identifier
    
    Returns:
        Status message
    
    Raises:
        HTTPException: If bot not found or cannot pause
    """
    try:
        await orchestrator.pause_bot(bot_id)
        return {"status": "paused", "bot_id": str(bot_id)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause bot: {str(e)}",
        )


@router.put("/{bot_id}/config", response_model=BotResponse)
async def update_bot_config(
    bot_id: int,
    config: BotConfigUpdate,
    bot_repo=Depends(get_bot_repository),
) -> BotResponse:
    """Update bot configuration.
    
    Args:
        bot_id: Bot identifier
        config: New configuration values
    
    Returns:
        Updated bot details
    
    Raises:
        HTTPException: If bot not found or config invalid
    """
    bot = await bot_repo.find_by_id(bot_id)
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot {bot_id} not found",
        )
    
    # Update config
    bot.config.update(config.config)
    await bot_repo.update(bot)
    
    return BotResponse.model_validate(bot)
