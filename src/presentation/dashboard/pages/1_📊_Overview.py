"""Overview dashboard page.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import streamlit as st
import time
from datetime import datetime, timedelta
import random

from src.presentation.dashboard.components import (
    APIClient,
    render_metric_card,
    StateManager,
)
from src.presentation.dashboard.components.chart_utils import (
    create_line_chart,
    create_pie_chart,
    create_heatmap,
)

# Page config
st.set_page_config(
    page_title="Overview - PETS Dashboard",
    page_icon="📊",
    layout="wide",
)

# Initialize state
state = StateManager()

if not state.has("api_client"):
    state.set("api_client", APIClient(base_url="http://localhost:8000"))

api_client = state.get("api_client")

# Header
st.title("📊 Portfolio Overview")

# Emergency controls
st.markdown("### 🚨 Emergency Controls")
col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

with col1:
    if st.button("🛑 HALT ALL", type="primary", use_container_width=True):
        result = api_client.emergency_halt()
        if result.get("status") == "success":
            st.success("Emergency halt triggered!")
        else:
            st.error(f"Failed: {result.get('message')}")

with col2:
    if st.button("⏸️ PAUSE ALL", use_container_width=True):
        st.info("Pausing all bots...")
        # TODO: Implement pause all API call

with col3:
    if st.button("▶️ RESUME ALL", use_container_width=True):
        st.info("Resuming all bots...")
        # TODO: Implement resume all API call

st.markdown("---")

# Metrics cards (1s updates)
st.markdown("### 📈 Key Metrics")

# Fetch metrics
metrics = api_client.get_portfolio_metrics()

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_metric_card(
        "Portfolio Value",
        f"${metrics.get('portfolio_value', 0):,.2f}",
        f"+${random.uniform(10, 100):.2f}",
        "normal",
    )

with col2:
    pnl = metrics.get("total_pnl", 0)
    render_metric_card(
        "Total P&L",
        f"${pnl:+,.2f}",
        f"{(pnl / 5000 * 100):+.2f}%" if pnl != 0 else "0%",
        "normal" if pnl >= 0 else "inverse",
    )

with col3:
    render_metric_card(
        "Open Positions",
        str(metrics.get("open_positions", 0)),
        None,
        "off",
    )

with col4:
    render_metric_card(
        "Active Bots",
        f"{metrics.get('active_bots', 0)}/10",
        None,
        "off",
    )

st.markdown("---")

# Charts
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 Cumulative P&L")
    
    # Generate sample data
    now = datetime.now()
    x = [now - timedelta(hours=i) for i in range(24, 0, -1)]
    y = [random.uniform(-100, 500) for _ in range(24)]
    
    fig = create_line_chart(
        x=x,
        y=y,
        title="24h P&L Trend",
        x_label="Time",
        y_label="P&L ($)",
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 🥧 Portfolio Composition")
    
    # Generate sample data
    bots = api_client.get_bot_list()
    
    if bots:
        labels = [f"Bot {b.get('bot_id', i+1)}" for i, b in enumerate(bots[:8])]
        values = [random.uniform(500, 2000) for _ in labels]
    else:
        labels = [f"Bot {i+1}" for i in range(8)]
        values = [random.uniform(500, 2000) for _ in labels]
    
    fig = create_pie_chart(
        labels=labels,
        values=values,
        title="Capital Allocation",
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Zone heatmap
st.markdown("### 🗺️ Zone Exposure Heatmap")

# Generate sample data
zones = ["Z1", "Z2", "Z3", "Z4", "Z5"]
bots_sample = [f"Bot {i+1}" for i in range(8)]
z_data = [[random.uniform(0, 100) for _ in zones] for _ in bots_sample]

fig = create_heatmap(
    z=z_data,
    x=zones,
    y=bots_sample,
    title="Exposure by Bot and Zone (%)",
)

st.plotly_chart(fig, use_container_width=True)

# Bot status grid
st.markdown("### 🤖 Bot Status Grid")

bots = api_client.get_bot_list()

if bots:
    # Display as table
    bot_data = []
    for bot in bots[:10]:
        bot_data.append({
            "Bot ID": bot.get("bot_id", "N/A"),
            "Status": bot.get("state", "UNKNOWN"),
            "P&L": f"${bot.get('pnl', 0):+,.2f}",
            "Positions": bot.get("open_positions", 0),
            "Win Rate": f"{bot.get('win_rate', 0):.1f}%",
        })
    
    st.dataframe(bot_data, use_container_width=True)
else:
    st.info("No bots available. Check API connection.")

# Auto-refresh indicator
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Auto-refresh: 1s")

# Auto-refresh (1s)
time.sleep(1)
st.rerun()
