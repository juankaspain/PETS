"""Dashboard utility functions.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from datetime import datetime


def format_currency(amount: float, decimals: int = 2) -> str:
    """Format currency with $ and thousands separator.
    
    Args:
        amount: Amount to format
        decimals: Decimal places
        
    Returns:
        Formatted currency string
    """
    return f"${amount:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage.
    
    Args:
        value: Value to format (0.1234 = 12.34%)
        decimals: Decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"


def format_timestamp(timestamp: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format timestamp to human-readable string.
    
    Args:
        timestamp: Datetime to format
        fmt: strftime format string
        
    Returns:
        Formatted timestamp string
    """
    return timestamp.strftime(fmt)


def calculate_pnl(entry_price: float, current_price: float, size: float, side: str) -> float:
    """Calculate profit/loss.
    
    Args:
        entry_price: Entry price
        current_price: Current market price
        size: Position size
        side: Position side (YES/NO)
        
    Returns:
        Profit/loss amount
    """
    if side.upper() == "YES":
        return (current_price - entry_price) * size
    else:
        return (entry_price - current_price) * size


def calculate_roi(pnl: float, investment: float) -> float:
    """Calculate return on investment.
    
    Args:
        pnl: Profit/loss
        investment: Initial investment
        
    Returns:
        ROI as decimal (0.10 = 10%)
    """
    if investment == 0:
        return 0.0
    return pnl / investment


def get_zone_color(zone: int) -> str:
    """Get color for price zone.
    
    Args:
        zone: Zone number (1-5)
        
    Returns:
        Color name for Streamlit
    """
    colors = {
        1: "green",
        2: "blue",
        3: "orange",
        4: "red",
        5: "red",
    }
    return colors.get(zone, "gray")


def get_status_color(status: str) -> str:
    """Get color for order/position status.
    
    Args:
        status: Status string
        
    Returns:
        Color name for Streamlit
    """
    status_upper = status.upper()
    
    if status_upper in ["FILLED", "ACTIVE", "COMPLETED"]:
        return "green"
    elif status_upper in ["PENDING", "STARTING", "STOPPING"]:
        return "orange"
    elif status_upper in ["CANCELED", "REJECTED", "ERROR", "EMERGENCY_HALT"]:
        return "red"
    elif status_upper in ["PAUSED", "STOPPED"]:
        return "gray"
    else:
        return "blue"


def get_bot_state_emoji(state: str) -> str:
    """Get emoji for bot state.
    
    Args:
        state: Bot state
        
    Returns:
        Emoji character
    """
    emojis = {
        "IDLE": "⚪",
        "STARTING": "🟡",
        "ACTIVE": "🟢",
        "PAUSED": "🟠",
        "STOPPING": "🟡",
        "STOPPED": "⚫",
        "ERROR": "🔴",
        "EMERGENCY_HALT": "🔴",
    }
    return emojis.get(state.upper(), "⚪")
