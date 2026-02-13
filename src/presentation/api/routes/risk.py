"""Risk management routes.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.application.use_cases import EmergencyHaltUseCase
from src.presentation.api.dependencies import (
    get_emergency_halt_use_case,
    get_risk_manager,
)
from src.presentation.api.schemas import (
    CircuitBreakerStatus,
    EmergencyHaltRequest,
    RiskMetrics,
)

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/metrics", response_model=RiskMetrics)
async def get_risk_metrics(
    bot_id: int | None = Query(None, description="Bot ID (None for portfolio)"),
    risk_manager=Depends(get_risk_manager),
) -> RiskMetrics:
    """Get risk metrics.
    
    Args:
        bot_id: Optional bot filter (None for portfolio-wide)
    
    Returns:
        Risk metrics including drawdown, exposure, consecutive losses
    """
    if bot_id:
        metrics = await risk_manager.get_bot_risk_metrics(bot_id)
    else:
        metrics = await risk_manager.get_portfolio_risk_metrics()
    
    return RiskMetrics.model_validate(metrics)


@router.get("/circuit-breakers", response_model=list[CircuitBreakerStatus])
async def get_circuit_breakers(
    risk_manager=Depends(get_risk_manager),
) -> list[CircuitBreakerStatus]:
    """Get circuit breaker status.
    
    Returns:
        List of all circuit breakers with current status
    """
    breakers = await risk_manager.get_circuit_breaker_status()
    return [CircuitBreakerStatus.model_validate(b) for b in breakers]


@router.post("/emergency-halt", status_code=status.HTTP_202_ACCEPTED)
async def emergency_halt(
    request: EmergencyHaltRequest,
    halt_use_case: EmergencyHaltUseCase = Depends(get_emergency_halt_use_case),
) -> dict[str, str]:
    """Trigger emergency halt.
    
    Args:
        request: Halt configuration
    
    Returns:
        Status message
    
    Raises:
        HTTPException: If halt fails
    """
    try:
        await halt_use_case.execute(
            reason=request.reason,
            halt_all_bots=request.halt_all_bots,
            close_positions=request.close_positions,
        )
        return {
            "status": "halted",
            "reason": request.reason,
            "halt_all_bots": str(request.halt_all_bots),
            "close_positions": str(request.close_positions),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute emergency halt: {str(e)}",
        )
