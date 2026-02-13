"""Order management routes.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.application.use_cases import PlaceOrderUseCase
from src.presentation.api.dependencies import (
    get_order_repository,
    get_place_order_use_case,
)
from src.presentation.api.schemas import (
    OrderListResponse,
    OrderResponse,
    PlaceOrderRequest,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=OrderListResponse)
async def list_orders(
    bot_id: int | None = Query(None, description="Filter by bot ID"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    order_repo=Depends(get_order_repository),
) -> OrderListResponse:
    """List orders.
    
    Args:
        bot_id: Optional bot filter
        status: Optional status filter
        limit: Maximum results
    
    Returns:
        List of orders
    """
    if bot_id:
        orders = await order_repo.find_by_bot_id(bot_id, limit=limit)
    else:
        orders = await order_repo.find_all(limit=limit)
    
    # Filter by status if provided
    if status:
        orders = [o for o in orders if o.status.value == status]
    
    return OrderListResponse(
        orders=[OrderResponse.model_validate(o) for o in orders],
        total=len(orders),
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    order_repo=Depends(get_order_repository),
) -> OrderResponse:
    """Get order details.
    
    Args:
        order_id: Order identifier
    
    Returns:
        Order details
    
    Raises:
        HTTPException: If order not found
    """
    order = await order_repo.find_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )
    return OrderResponse.model_validate(order)


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(
    request: PlaceOrderRequest,
    place_use_case: PlaceOrderUseCase = Depends(get_place_order_use_case),
) -> OrderResponse:
    """Place new order.
    
    Args:
        request: Order placement request
    
    Returns:
        Created order details
    
    Raises:
        HTTPException: If order rejected or validation fails
    """
    try:
        order = await place_use_case.execute(
            bot_id=request.bot_id,
            market_id=request.market_id,
            side=request.side,
            price=request.price,
            size=request.size,
            post_only=request.post_only,
        )
        return OrderResponse.model_validate(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to place order: {str(e)}",
        )
