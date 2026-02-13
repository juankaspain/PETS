"""Wallet management routes.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.application.use_cases import (
    RebalanceWalletUseCase,
    TopUpWalletUseCase,
)
from src.presentation.api.dependencies import (
    get_rebalance_wallet_use_case,
    get_topup_wallet_use_case,
    get_wallet_repository,
)
from src.presentation.api.schemas import (
    RebalanceWalletRequest,
    TopUpWalletRequest,
    TransactionResponse,
    WalletBalanceResponse,
)

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("/balance", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    wallet_repo=Depends(get_wallet_repository),
) -> WalletBalanceResponse:
    """Get wallet balance.
    
    Returns:
        Current USDC and MATIC balances
    """
    wallet = await wallet_repo.get_hot_wallet()
    return WalletBalanceResponse(
        address=wallet.address,
        usdc_balance=wallet.balance_usdc,
        matic_balance=wallet.balance_matic,
        pending_transactions=len(wallet.pending_transactions),
        last_sync_at=wallet.last_sync_at,
    )


@router.post("/topup", response_model=TransactionResponse, status_code=status.HTTP_202_ACCEPTED)
async def topup_wallet(
    request: TopUpWalletRequest,
    topup_use_case: TopUpWalletUseCase = Depends(get_topup_wallet_use_case),
) -> TransactionResponse:
    """Top up hot wallet from cold wallet.
    
    Args:
        request: Top up amount and source
    
    Returns:
        Transaction details
    
    Raises:
        HTTPException: If top up fails
    """
    try:
        tx = await topup_use_case.execute(
            amount_usdc=request.amount_usdc,
            from_cold_wallet=request.from_cold_wallet,
        )
        return TransactionResponse.model_validate(tx)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to top up wallet: {str(e)}",
        )


@router.post("/rebalance", response_model=TransactionResponse, status_code=status.HTTP_202_ACCEPTED)
async def rebalance_wallet(
    request: RebalanceWalletRequest,
    rebalance_use_case: RebalanceWalletUseCase = Depends(get_rebalance_wallet_use_case),
) -> TransactionResponse:
    """Auto-rebalance hot/cold wallet split.
    
    Args:
        request: Target hot wallet percentage
    
    Returns:
        Transaction details
    
    Raises:
        HTTPException: If rebalance fails
    """
    try:
        tx = await rebalance_use_case.execute(
            target_hot_percentage=request.target_hot_percentage,
        )
        return TransactionResponse.model_validate(tx)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rebalance wallet: {str(e)}",
        )


@router.get("/transactions", response_model=list[TransactionResponse])
async def get_transactions(
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    wallet_repo=Depends(get_wallet_repository),
) -> list[TransactionResponse]:
    """Get recent wallet transactions.
    
    Args:
        limit: Maximum results
    
    Returns:
        List of recent transactions
    """
    transactions = await wallet_repo.get_recent_transactions(limit=limit)
    return [TransactionResponse.model_validate(tx) for tx in transactions]
