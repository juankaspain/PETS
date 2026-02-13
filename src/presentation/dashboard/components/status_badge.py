"""Status badge components.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import streamlit as st

from src.presentation.dashboard.utils import (
    get_bot_state_emoji,
    get_status_color,
    get_zone_color,
)


def bot_status_badge(state: str) -> None:
    """Display bot status badge.
    
    Args:
        state: Bot state
    """
    emoji = get_bot_state_emoji(state)
    color = get_status_color(state)
    
    st.markdown(
        f'<span style="color: {color};">{emoji} {state}</span>',
        unsafe_allow_html=True,
    )


def zone_badge(zone: int) -> None:
    """Display zone badge.
    
    Args:
        zone: Zone number (1-5)
    """
    color = get_zone_color(zone)
    
    st.markdown(
        f'<span style="background-color: {color}; padding: 2px 8px; '
        f'border-radius: 4px; color: white;">Z{zone}</span>',
        unsafe_allow_html=True,
    )
