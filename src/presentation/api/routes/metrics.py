"""Metrics routes.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse

from src.presentation.api.dependencies import (
    get_metrics_service,
    get_prometheus_exporter,
)
from src.presentation.api.schemas import (
    BotMetrics,
    PortfolioMetrics,
)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/bots/{bot_id}", response_model=BotMetrics)
async def get_bot_metrics(
    bot_id: int,
    metrics_service=Depends(get_metrics_service),
) -> BotMetrics:
    """Get bot performance metrics.
    
    Args:
        bot_id: Bot identifier
    
    Returns:
        Bot metrics including P&L, win rate, Sharpe ratio
    
    Raises:
        HTTPException: If bot not found
    """
    try:
        metrics = await metrics_service.get_bot_metrics(bot_id)
        return BotMetrics.model_validate(metrics)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/portfolio", response_model=PortfolioMetrics)
async def get_portfolio_metrics(
    metrics_service=Depends(get_metrics_service),
) -> PortfolioMetrics:
    """Get portfolio-wide metrics.
    
    Returns:
        Portfolio metrics including total P&L, ROI, active bots
    """
    metrics = await metrics_service.get_portfolio_metrics()
    return PortfolioMetrics.model_validate(metrics)


@router.get("/prometheus", response_class=PlainTextResponse)
async def get_prometheus_metrics(
    exporter=Depends(get_prometheus_exporter),
) -> str:
    """Get metrics in Prometheus format.
    
    Returns:
        Metrics in Prometheus exposition format
    """
    return await exporter.export()
