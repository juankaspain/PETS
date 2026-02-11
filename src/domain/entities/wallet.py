"""Wallet entity - Wallet balance and nonce tracking."""

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal

from src.domain.exceptions import InsufficientGasError, InsufficientUSDCError


@dataclass(frozen=True)
class Wallet:
    """Wallet entity with balance tracking.

    Represents a blockchain wallet with USDC and MATIC balances.
    Tracks nonce for transaction management.

    Attributes:
        address: Wallet address (0x prefixed hex)
        balance_usdc: USDC balance (6 decimals)
        balance_matic: MATIC balance (18 decimals)
        nonce: Current transaction nonce
        last_sync_at: Last blockchain sync timestamp
        is_hot_wallet: True if hot wallet, False if cold wallet
    """

    address: str
    balance_usdc: Decimal
    balance_matic: Decimal
    nonce: int
    last_sync_at: datetime
    is_hot_wallet: bool = True

    def __post_init__(self) -> None:
        """Validate wallet attributes.

        Raises:
            DomainError: If validation fails
        """
        if not self.address.startswith("0x") or len(self.address) != 42:
            from src.domain.exceptions import DomainError

            raise DomainError(
                f"Invalid wallet address: {self.address}",
                expected_format="0x + 40 hex chars",
            )

        if self.balance_usdc < Decimal("0"):
            from src.domain.exceptions import DomainError

            raise DomainError(f"USDC balance cannot be negative: {self.balance_usdc}")

        if self.balance_matic < Decimal("0"):
            from src.domain.exceptions import DomainError

            raise DomainError(
                f"MATIC balance cannot be negative: {self.balance_matic}"
            )

        if self.nonce < 0:
            from src.domain.exceptions import DomainError

            raise DomainError(f"Nonce cannot be negative: {self.nonce}")

    def update_balances(
        self, usdc: Decimal, matic: Decimal, timestamp: datetime
    ) -> "Wallet":
        """Update wallet balances.

        Args:
            usdc: New USDC balance
            matic: New MATIC balance
            timestamp: Update timestamp

        Returns:
            New Wallet instance with updated balances
        """
        return replace(
            self,
            balance_usdc=usdc,
            balance_matic=matic,
            last_sync_at=timestamp,
        )

    def increment_nonce(self) -> "Wallet":
        """Increment transaction nonce.

        Returns:
            New Wallet instance with incremented nonce
        """
        return replace(self, nonce=self.nonce + 1)

    def set_nonce(self, new_nonce: int, timestamp: datetime) -> "Wallet":
        """Set nonce (after blockchain sync).

        Args:
            new_nonce: New nonce value
            timestamp: Sync timestamp

        Returns:
            New Wallet instance with updated nonce
        """
        return replace(self, nonce=new_nonce, last_sync_at=timestamp)

    def check_usdc_balance(self, required: Decimal) -> None:
        """Check if wallet has sufficient USDC.

        Args:
            required: Required USDC amount

        Raises:
            InsufficientUSDCError: If balance insufficient
        """
        if self.balance_usdc < required:
            raise InsufficientUSDCError(
                f"Insufficient USDC: have {self.balance_usdc}, need {required}",
                wallet_address=self.address,
                balance=float(self.balance_usdc),
                required=float(required),
            )

    def check_gas_balance(self, required: Decimal) -> None:
        """Check if wallet has sufficient MATIC for gas.

        Args:
            required: Required MATIC amount for gas

        Raises:
            InsufficientGasError: If balance insufficient
        """
        if self.balance_matic < required:
            raise InsufficientGasError(
                f"Insufficient MATIC for gas: have {self.balance_matic}, need {required}",
                wallet_address=self.address,
                balance=float(self.balance_matic),
                required=float(required),
            )

    @property
    def needs_rebalance(self) -> bool:
        """Check if hot wallet needs rebalancing.

        Hot wallet should maintain 10-20% of capital.
        Rebalance if USDC < $5,000 (threshold for min operations).

        Returns:
            True if balance below rebalance threshold
        """
        if not self.is_hot_wallet:
            return False
        return self.balance_usdc < Decimal("5000")

    @property
    def balance_critical(self) -> bool:
        """Check if balance is critically low.

        Returns:
            True if USDC < $1,000 or MATIC < 1.0
        """
        return self.balance_usdc < Decimal("1000") or self.balance_matic < Decimal(
            "1.0"
        )

    def __str__(self) -> str:
        """String representation."""
        wallet_type = "HOT" if self.is_hot_wallet else "COLD"
        return (
            f"Wallet {self.address[:10]}... ({wallet_type}): "
            f"{self.balance_usdc:.2f} USDC, {self.balance_matic:.4f} MATIC"
        )

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"Wallet(address='{self.address}', "
            f"usdc={self.balance_usdc}, matic={self.balance_matic}, "
            f"nonce={self.nonce})"
        )
