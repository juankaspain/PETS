"""Tests for dashboard utilities.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from datetime import datetime

from src.presentation.dashboard.utils import (
    format_currency,
    format_market_id,
    format_percentage,
    format_timestamp,
)


def test_format_currency():
    """Test currency formatting."""
    assert format_currency(1234.56) == "$1,234.56"
    assert format_currency(-500.5) == "-$500.50"
    assert format_currency(0) == "$0.00"
    assert format_currency(1000000) == "$1,000,000.00"


def test_format_percentage():
    """Test percentage formatting."""
    assert format_percentage(0.1234) == "12.34%"
    assert format_percentage(-0.05) == "-5.00%"
    assert format_percentage(0) == "0.00%"
    assert format_percentage(1.0) == "100.00%"


def test_format_timestamp():
    """Test timestamp formatting."""
    dt = datetime(2026, 2, 13, 2, 20, 30)
    assert format_timestamp(dt) == "2026-02-13 02:20:30"
    assert format_timestamp(None) == "N/A"


def test_format_market_id():
    """Test market ID truncation."""
    long_id = "0x1234567890abcdef1234567890abcdef"
    assert format_market_id(long_id, 16) == "0x1234567890ab..."
    
    short_id = "short_id"
    assert format_market_id(short_id) == "short_id"
    
    assert format_market_id(long_id, 32) == long_id
