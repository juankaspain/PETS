"""Domain protocols (interfaces)."""

from src.domain.protocols.repositories import (
    BotRepository,
    MarketRepository,
    OrderRepository,
    PositionRepository,
    WalletRepository,
)

__all__ = [
    "BotRepository",
    "OrderRepository",
    "PositionRepository",
    "MarketRepository",
    "WalletRepository",
]
