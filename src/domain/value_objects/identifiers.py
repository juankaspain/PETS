"""Identifier value objects with validation."""

import re
from typing import NewType

from src.domain.exceptions import InvalidOrderError

# UUID format for order IDs
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)

# Hex format for market IDs (Polymarket uses hex strings)
HEX_PATTERN = re.compile(r"^0x[0-9a-fA-F]+$")


OrderId = NewType("OrderId", str)


def validate_order_id(order_id: str) -> OrderId:
    """Validate and create OrderId.

    Args:
        order_id: Order ID string (must be valid UUID)

    Returns:
        Validated OrderId

    Raises:
        InvalidOrderError: If order_id is not valid UUID format

    Example:
        >>> order_id = validate_order_id("550e8400-e29b-41d4-a716-446655440000")
        >>> isinstance(order_id, str)
        True
    """
    if not UUID_PATTERN.match(order_id):
        raise InvalidOrderError(
            f"Invalid order_id format: {order_id}", expected="UUID v4"
        )
    return OrderId(order_id)


MarketId = NewType("MarketId", str)


def validate_market_id(market_id: str) -> MarketId:
    """Validate and create MarketId.

    Args:
        market_id: Market ID string (must be valid hex format)

    Returns:
        Validated MarketId

    Raises:
        InvalidOrderError: If market_id is not valid hex format

    Example:
        >>> market_id = validate_market_id("0x1234567890abcdef")
        >>> isinstance(market_id, str)
        True
    """
    if not HEX_PATTERN.match(market_id):
        raise InvalidOrderError(
            f"Invalid market_id format: {market_id}", expected="0x prefixed hex"
        )
    return MarketId(market_id)
