"""Dashboard utility functions.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from datetime import datetime
from typing import Optional


def format_currency(amount: float) -> str:
    """Format amount as USD currency.
    
    Args:
        amount: Amount in dollars
    
    Returns:
        Formatted string: $X,XXX.XX
    
    Examples:
        >>> format_currency(1234.56)
        '$1,234.56'
        >>> format_currency(-500.5)
        '-$500.50'
    """
    if amount < 0:
        return f"-${abs(amount):,.2f}"
    return f"${amount:,.2f}"


def format_percentage(value: float) -> str:
    """Format value as percentage.
    
    Args:
        value: Value as decimal (0.15 = 15%)
    
    Returns:
        Formatted string: X.XX%
    
    Examples:
        >>> format_percentage(0.1234)
        '12.34%'
        >>> format_percentage(-0.05)
        '-5.00%'
    """
    return f"{value * 100:.2f}%"


def format_timestamp(timestamp: Optional[datetime]) -> str:
    """Format timestamp as ISO 8601 string.
    
    Args:
        timestamp: Datetime object or None
    
    Returns:
        Formatted string: YYYY-MM-DD HH:MM:SS or "N/A"
    
    Examples:
        >>> format_timestamp(datetime(2026, 2, 13, 2, 20, 30))
        '2026-02-13 02:20:30'
        >>> format_timestamp(None)
        'N/A'
    """
    if timestamp is None:
        return "N/A"
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def format_market_id(market_id: str, max_length: int = 16) -> str:
    """Truncate long market IDs.
    
    Args:
        market_id: Full market ID (Polymarket condition ID)
        max_length: Maximum length before truncation
    
    Returns:
        Truncated string with ellipsis
    
    Examples:
        >>> format_market_id("0x1234567890abcdef1234567890abcdef")
        '0x1234567890ab...'
        >>> format_market_id("short_id")
        'short_id'
    """
    if len(market_id) <= max_length:
        return market_id
    return market_id[:max_length] + "..."
