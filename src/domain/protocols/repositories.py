"""Repository protocol interfaces."""

from decimal import Decimal
from typing import Optional, Protocol
from uuid import UUID


class BotRepository(Protocol):
    """Bot repository interface."""

    async def create(
        self,
        strategy_type: str,
        config: dict,
        capital_allocated: Decimal,
    ) -> int:
        """Create new bot."""
        ...

    async def get_by_id(self, bot_id: int) -> Optional[dict]:
        """Get bot by ID."""
        ...

    async def update_state(self, bot_id: int, state: str) -> None:
        """Update bot state."""
        ...


class OrderRepository(Protocol):
    """Order repository interface."""

    async def create(
        self,
        bot_id: int,
        market_id: str,
        side: str,
        size: Decimal,
        price: Decimal,
        zone: int,
        post_only: bool = True,
    ) -> UUID:
        """Create new order."""
        ...

    async def get_by_id(self, order_id: UUID) -> Optional[dict]:
        """Get order by ID."""
        ...

    async def update_status(self, order_id: UUID, status: str) -> None:
        """Update order status."""
        ...

    async def get_by_bot(
        self,
        bot_id: int,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get orders for bot."""
        ...


class PositionRepository(Protocol):
    """Position repository interface."""

    async def create(
        self,
        bot_id: int,
        order_id: UUID,
        market_id: str,
        side: str,
        size: Decimal,
        entry_price: Decimal,
        zone: int,
    ) -> UUID:
        """Create new position."""
        ...

    async def get_by_id(self, position_id: UUID) -> Optional[dict]:
        """Get position by ID."""
        ...

    async def update_pnl(
        self,
        position_id: UUID,
        current_price: Optional[Decimal] = None,
        realized: Optional[Decimal] = None,
        unrealized: Optional[Decimal] = None,
    ) -> None:
        """Update position P&L."""
        ...

    async def close(self, position_id: UUID, realized_pnl: Decimal) -> None:
        """Close position."""
        ...

    async def get_open(
        self, bot_id: Optional[int] = None, limit: int = 100
    ) -> list[dict]:
        """Get open positions."""
        ...


class MarketRepository(Protocol):
    """Market repository interface."""

    async def upsert(
        self,
        market_id: str,
        question: str,
        outcomes: list[str],
        liquidity: Decimal,
        volume_24h: Optional[Decimal] = None,
        yes_price: Optional[Decimal] = None,
        no_price: Optional[Decimal] = None,
        resolves_at: Optional[str] = None,
    ) -> None:
        """Insert or update market."""
        ...

    async def get_by_id(self, market_id: str) -> Optional[dict]:
        """Get market by ID."""
        ...

    async def get_active(self, limit: int = 100) -> list[dict]:
        """Get active markets."""
        ...


class WalletRepository(Protocol):
    """Wallet repository interface."""

    async def update_balance(
        self,
        address: str,
        token: str,
        balance: Decimal,
        ttl: int = 300,
    ) -> None:
        """Update wallet balance."""
        ...

    async def get_balance(
        self,
        address: str,
        token: str,
    ) -> Optional[Decimal]:
        """Get wallet balance."""
        ...
