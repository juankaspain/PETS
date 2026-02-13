"""Wallet API schemas.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class WalletBalanceResponse(BaseModel):
    """Wallet balance response."""

    address: str = Field(..., description="Wallet address")
    usdc_balance: Decimal = Field(..., description="USDC balance")
    matic_balance: Decimal = Field(..., description="MATIC balance")
    pending_transactions: int = Field(..., description="Number of pending txs")
    last_sync_at: datetime = Field(..., description="Last sync timestamp")


class TopUpWalletRequest(BaseModel):
    """Top up wallet request."""

    amount_usdc: Decimal = Field(..., gt=0, description="Amount to transfer (USDC)")
    from_cold_wallet: bool = Field(True, description="Transfer from cold wallet")


class RebalanceWalletRequest(BaseModel):
    """Rebalance wallet request."""

    target_hot_percentage: Decimal = Field(
        Decimal("0.15"),
        ge=Decimal("0.10"),
        le=Decimal("0.20"),
        description="Target hot wallet percentage",
    )


class TransactionResponse(BaseModel):
    """Transaction details response."""

    tx_hash: str = Field(..., description="Transaction hash")
    from_address: str = Field(..., description="From address")
    to_address: str = Field(..., description="To address")
    amount: Decimal = Field(..., description="Amount transferred")
    gas_cost: Decimal = Field(..., description="Gas cost (USDC)")
    status: str = Field(..., description="Transaction status")
    timestamp: datetime = Field(..., description="Transaction timestamp")

    class Config:
        from_attributes = True
