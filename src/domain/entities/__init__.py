"""Domain entities - Core business objects with identity.

Entities are distinguished by their identity, not their attributes.
Two entities with same attributes but different IDs are different.

All entities are immutable (frozen dataclasses).
Modifications create new instances via helper methods.
"""

from src.domain.entities.bot import Bot
from src.domain.entities.market import Market
from src.domain.entities.order import Order
from src.domain.entities.position import Position
from src.domain.entities.trade import Trade
from src.domain.entities.wallet import Wallet

__all__ = [
    "Bot",
    "Market",
    "Order",
    "Position",
    "Trade",
    "Wallet",
]
