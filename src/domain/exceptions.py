"""Domain exceptions hierarchy.

All domain exceptions inherit from PETSError base class.
Provides structured error handling with context.
"""

from typing import Any


class PETSError(Exception):
    """Base exception for all PETS errors."""

    def __init__(self, message: str, **context: Any) -> None:
        """Initialize exception with message and context.

        Args:
            message: Human-readable error description
            **context: Additional context key-value pairs
        """
        super().__init__(message)
        self.message = message
        self.context = context

    def __str__(self) -> str:
        """String representation with context."""
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} ({context_str})"
        return self.message


class DomainError(PETSError):
    """Base class for domain logic errors."""


class InfrastructureError(PETSError):
    """Base class for infrastructure errors (DB, network, etc)."""


class ApplicationError(PETSError):
    """Base class for application layer errors."""


# Order Errors
class OrderError(DomainError):
    """Base class for order-related errors."""


class InvalidOrderError(OrderError):
    """Order validation failed.

    Raised when:
    - Invalid price range
    - Invalid size
    - Missing required fields
    """


class InsufficientBalanceError(OrderError):
    """Insufficient balance to place order.

    Raised when:
    - USDC balance < order value
    - MATIC balance < estimated gas
    """


class OrderRejectedError(OrderError):
    """Order rejected by exchange.

    Raised when:
    - Polymarket CLOB rejects order
    - Rate limit exceeded
    - Market closed
    """


class DuplicateOrderError(OrderError):
    """Duplicate order detected.

    Raised when:
    - Same order_id already exists
    - Identical order within short timeframe
    """


# Position Errors
class PositionError(DomainError):
    """Base class for position-related errors."""


class PositionNotFoundError(PositionError):
    """Position not found in repository."""


class PositionAlreadyClosedError(PositionError):
    """Attempt to modify already closed position."""


# Risk Violations
class RiskViolation(DomainError):
    """Base class for risk management violations."""


class ZoneViolationError(RiskViolation):
    """Order violates zone restrictions.

    Raised when:
    - Directional order in Zone 4-5 (0.60-0.98)
    - Zone 3 (0.40-0.60) without edge calculation
    """


class DrawdownExceededError(RiskViolation):
    """Drawdown threshold exceeded.

    Raised when:
    - Bot drawdown > 25%
    - Portfolio drawdown > 40%
    - Daily loss > 5%
    """


class ExposureLimitError(RiskViolation):
    """Position exposure limit exceeded.

    Raised when:
    - Single position > max size
    - Total exposure > limit
    - Correlation exposure too high
    """


class ConsecutiveLossesError(RiskViolation):
    """Consecutive losses threshold exceeded.

    Raised when:
    - Bot has 3+ consecutive losses
    - Triggers 24h pause
    """


class CircuitBreakerOpenError(RiskViolation):
    """Circuit breaker is open, trading halted.

    Raised when:
    - Emergency halt triggered
    - Manual intervention required
    """


# Wallet Errors
class WalletError(DomainError):
    """Base class for wallet-related errors."""


class InsufficientGasError(WalletError):
    """Insufficient MATIC for gas fees."""


class InsufficientUSDCError(WalletError):
    """Insufficient USDC for order."""


class NonceOutOfSyncError(WalletError):
    """Wallet nonce out of sync with blockchain.

    Raised when:
    - Local nonce != blockchain nonce
    - Requires resync
    """


class WalletLockedError(WalletError):
    """Wallet is locked and cannot sign transactions.

    Raised when:
    - Cold wallet access attempted without authorization
    - Wallet in emergency mode
    """
