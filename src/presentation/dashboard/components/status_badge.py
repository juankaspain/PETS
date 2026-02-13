"""Status badge components.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import streamlit as st


def bot_status_badge(state: str) -> None:
    """Render bot status badge.
    
    Args:
        state: Bot state (IDLE, RUNNING, PAUSED, ERROR)
    """
    colors = {
        "IDLE": "gray",
        "RUNNING": "green",
        "PAUSED": "orange",
        "ERROR": "red",
    }
    
    color = colors.get(state, "gray")
    st.markdown(
        f'<span style="background-color:{color};color:white;'
        f'padding:4px 8px;border-radius:4px;font-size:12px;'
        f'font-weight:bold">{state}</span>',
        unsafe_allow_html=True,
    )


def zone_badge(zone: int) -> None:
    """Render risk zone badge.
    
    Args:
        zone: Risk zone 1-5
    """
    # Zone colors: 1=green, 2=blue, 3=orange, 4=red, 5=darkred
    colors = {
        1: "green",
        2: "blue",
        3: "orange",
        4: "red",
        5: "darkred",
    }
    
    color = colors.get(zone, "gray")
    st.markdown(
        f'<span style="background-color:{color};color:white;'
        f'padding:4px 8px;border-radius:4px;font-size:12px;'
        f'font-weight:bold">Z{zone}</span>',
        unsafe_allow_html=True,
    )


def order_status_badge(status: str) -> None:
    """Render order status badge.
    
    Args:
        status: Order status
    """
    colors = {
        "PENDING": "orange",
        "FILLED": "green",
        "PARTIALLY_FILLED": "blue",
        "CANCELED": "gray",
        "REJECTED": "red",
    }
    
    color = colors.get(status, "gray")
    st.markdown(
        f'<span style="background-color:{color};color:white;'
        f'padding:4px 8px;border-radius:4px;font-size:12px;'
        f'font-weight:bold">{status}</span>',
        unsafe_allow_html=True,
    )
