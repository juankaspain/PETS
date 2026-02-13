"""Orders page.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import asyncio

import pandas as pd
import streamlit as st

from src.presentation.dashboard.api_client import APIClient
from src.presentation.dashboard.utils import format_currency, format_timestamp

st.set_page_config(page_title="Orders", page_icon="📜", layout="wide")

st.title("📜 Order Log")

# Initialize API client
if "api_client" not in st.session_state:
    st.session_state.api_client = APIClient()

api_client = st.session_state.api_client

# Filters
col1, col2 = st.columns(2)

with col1:
    bot_filter = st.selectbox(
        "Filter by bot",
        ["All"] + [f"Bot {i}" for i in range(1, 11)],
    )

with col2:
    status_filter = st.multiselect(
        "Filter by status",
        ["PENDING", "FILLED", "PARTIALLY_FILLED", "CANCELED", "REJECTED"],
        default=[],
    )


async def load_orders():
    """Load orders list."""
    try:
        bot_id = None if bot_filter == "All" else int(bot_filter.split()[1])
        result = await api_client.list_orders(bot_id=bot_id)
        orders = result.get("orders", [])
        
        # Filter by status
        if status_filter:
            orders = [o for o in orders if o.get("status") in status_filter]
        
        return orders
    except Exception as e:
        st.error(f"Error loading orders: {e}")
        return []


orders = asyncio.run(load_orders())

if not orders:
    st.info("No orders found.")
else:
    # Orders table
    df_data = []
    for order in orders:
        df_data.append({
            "Order ID": order.get("order_id", "N/A")[:8] + "...",
            "Bot ID": order.get("bot_id"),
            "Market": order.get("market_id", "N/A")[:16] + "...",
            "Side": order.get("side"),
            "Size": order.get("size", 0),
            "Price": order.get("price", 0),
            "Status": order.get("status"),
            "Zone": order.get("zone", 0),
        })
    
    df = pd.DataFrame(df_data)
    
    st.dataframe(
        df.style.format({
            "Size": "{:,.2f}",
            "Price": "{:.4f}",
        }),
        use_container_width=True,
    )
    
    st.divider()
    
    # Summary
    st.subheader("Order Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Orders", len(orders))
    
    with col2:
        filled = sum(1 for o in orders if o.get("status") == "FILLED")
        st.metric("Filled", filled)
    
    with col3:
        pending = sum(1 for o in orders if o.get("status") == "PENDING")
        st.metric("Pending", pending)
    
    with col4:
        canceled = sum(1 for o in orders if o.get("status") in ["CANCELED", "REJECTED"])
        st.metric("Canceled/Rejected", canceled)
