"""Positions page.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import asyncio

import pandas as pd
import streamlit as st

from src.presentation.dashboard.api_client import APIClient
from src.presentation.dashboard.components.status_badge import zone_badge
from src.presentation.dashboard.utils import (
    format_currency,
    format_percentage,
    format_timestamp,
)

st.set_page_config(page_title="Positions", page_icon="💰", layout="wide")

st.title("💰 Active Positions")

# Initialize API client
if "api_client" not in st.session_state:
    st.session_state.api_client = APIClient()

api_client = st.session_state.api_client

# Filter
bot_filter = st.selectbox(
    "Filter by bot",
    ["All"] + [f"Bot {i}" for i in range(1, 11)],
)


async def load_positions():
    """Load positions list."""
    try:
        bot_id = None if bot_filter == "All" else int(bot_filter.split()[1])
        result = await api_client.list_positions(bot_id=bot_id)
        return result.get("positions", [])
    except Exception as e:
        st.error(f"Error loading positions: {e}")
        return []


positions = asyncio.run(load_positions())

if not positions:
    st.info("No active positions.")
else:
    # Positions table
    df_data = []
    for pos in positions:
        df_data.append({
            "Position ID": pos.get("position_id"),
            "Bot ID": pos.get("bot_id"),
            "Market": pos.get("market_id", "N/A")[:16] + "...",
            "Side": pos.get("side"),
            "Size": pos.get("size", 0),
            "Entry": pos.get("entry_price", 0),
            "Current": pos.get("current_price", 0),
            "P&L": pos.get("unrealized_pnl", 0),
            "Zone": pos.get("zone", 0),
        })
    
    df = pd.DataFrame(df_data)
    
    st.dataframe(
        df.style.format({
            "Size": "{:,.2f}",
            "Entry": "{:.4f}",
            "Current": "{:.4f}",
            "P&L": "${:,.2f}",
        }).applymap(
            lambda x: "color: green" if x > 0 else "color: red" if x < 0 else "",
            subset=["P&L"],
        ),
        use_container_width=True,
    )
    
    st.divider()
    
    # Summary
    st.subheader("Summary")
    
    col1, col2, col3 = st.columns(3)
    
    total_pnl = sum(pos.get("unrealized_pnl", 0) for pos in positions)
    
    with col1:
        st.metric("Active Positions", len(positions))
    
    with col2:
        st.metric("Total Unrealized P&L", format_currency(total_pnl))
    
    with col3:
        winning = sum(1 for pos in positions if pos.get("unrealized_pnl", 0) > 0)
        st.metric("Winning", f"{winning}/{len(positions)}")
