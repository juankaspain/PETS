"""Position management routes.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.application.use_cases import ClosePositionUseCase
from src.presentation.api.dependencies import (
    get_close_position_use_case,
    get_position_repository,
)
from src.presentation.api.schemas import (
    ClosePositionRequest,
    PositionListResponse,
    PositionResponse,
)

router = APIRouter(prefix="/positions", tags=["positions"])


@router.get("", response_model=PositionListResponse)
async def list_positions(
    bot_id: int | None = Query(None, description="Filter by bot ID"),
    status: str | None = Query(None, description="Filter by status (open/closed)"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    position_repo=Depends(get_position_repository),
) -> PositionListResponse:
    """List positions.
    
    Args:
        bot_id: Optional bot filter
        status: Optional status filter
        limit: Maximum results
    
    Returns:
        List of positions
    """
    if bot_id:
        if status == "open":
            positions = await position_repo.find_open_by_bot(bot_id)
        else:
            positions = await position_repo.find_by_bot_id(bot_id, limit=limit)
    else:
        positions = await position_repo.find_all(limit=limit)
    
    return PositionListResponse(
        positions=[PositionResponse.model_validate(p) for p in positions],
        total=len(positions),
    )


@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: str,
    position_repo=Depends(get_position_repository),
) -> PositionResponse:
    """Get position details.
    
    Args:
        position_id: Position identifier
    
    Returns:
        Position details
    
    Raises:
        HTTPException: If position not found
    """
    position = await position_repo.find_by_id(position_id)
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Position {position_id} not found",
        )
    return PositionResponse.model_validate(position)


@router.post("/{position_id}/close", status_code=status.HTTP_202_ACCEPTED)
async def close_position(
    position_id: str,
    request: ClosePositionRequest,
    close_use_case: ClosePositionUseCase = Depends(get_close_position_use_case),
) -> dict[str, str]:
    """Close position.
    
    Args:
        position_id: Position identifier
        request: Close request with optional reason
    
    Returns:
        Status message
    
    Raises:
        HTTPException: If position not found or cannot close
    """
    try:
        await close_use_case.execute(position_id, request.reason)
        return {"status": "closing", "position_id": position_id}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to close position: {str(e)}",
        )
