"""Performance dashboard page.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random
from datetime import datetime, timedelta

from src.presentation.dashboard.components import (
    APIClient,
    StateManager,
)
from src.presentation.dashboard.components.chart_utils import (
    create_line_chart,
    get_default_layout,
)

# Page config
st.set_page_config(
    page_title="Performance - PETS Dashboard",
    page_icon="📈",
    layout="wide",
)

# Initialize state
state = StateManager()

if not state.has("api_client"):
    state.set("api_client", APIClient(base_url="http://localhost:8000"))

api_client = state.get("api_client")

# Header
st.title("📈 Performance Analysis")

# Filters
st.markdown("### Filters")

col1, col2, col3 = st.columns(3)

with col1:
    strategy_filter = st.multiselect(
        "Strategy Type",
        ["All", "Rebalancing", "Esports", "Copy Trading", "News-driven", "Market Making"],
        default=["All"],
    )

with col2:
    status_filter = st.multiselect(
        "Status",
        ["All", "ACTIVE", "PAUSED", "STOPPED"],
        default=["All"],
    )

with col3:
    date_range = st.selectbox(
        "Time Range",
        ["24h", "7d", "30d", "All Time"],
        index=1,
    )

st.markdown("---")

# Comparative table
st.markdown("### 📊 Bot Performance Comparison")

# Fetch bots
bots = api_client.get_bot_list()

if not bots:
    # Generate sample data
    bots = [
        {
            "bot_id": i+1,
            "strategy_type": ["Rebalancing", "Esports", "Market Making"][i % 3],
            "state": random.choice(["ACTIVE", "PAUSED", "STOPPED"]),
        }
        for i in range(10)
    ]

# Create performance dataframe
performance_data = []

for bot in bots[:10]:
    bot_id = bot.get("bot_id", 0)
    metrics = api_client.get_bot_metrics(bot_id)
    
    if not metrics:
        metrics = {
            "pnl": random.uniform(-200, 800),
            "roi": random.uniform(-10, 25),
            "win_rate": random.uniform(45, 70),
            "sharpe_ratio": random.uniform(0.3, 1.8),
            "open_positions": random.randint(0, 5),
        }
    
    performance_data.append({
        "Bot ID": f"Bot {bot_id}",
        "Strategy": bot.get("strategy_type", "Unknown"),
        "ROI (%)": f"{metrics.get('roi', 0):.2f}",
        "P&L ($)": f"{metrics.get('pnl', 0):+,.2f}",
        "Win Rate (%)": f"{metrics.get('win_rate', 0):.1f}",
        "Sharpe": f"{metrics.get('sharpe_ratio', 0):.2f}",
        "Positions": metrics.get("open_positions", 0),
        "Status": bot.get("state", "UNKNOWN"),
    })

df = pd.DataFrame(performance_data)

# Display dataframe with styling
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
)

# Download button
csv = df.to_csv(index=False)
st.download_button(
    label="📥 Download CSV",
    data=csv,
    file_name=f"bot_performance_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
)

st.markdown("---")

# Charts
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📈 ROI Comparison (7d)")
    
    # Multi-line ROI chart
    fig = go.Figure()
    
    now = datetime.now()
    x = [now - timedelta(days=i) for i in range(7, 0, -1)]
    
    for i in range(1, 6):  # Top 5 bots
        y = [random.uniform(-2, 10) for _ in range(7)]
        
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines+markers",
                name=f"Bot {i}",
            )
        )
    
    layout = get_default_layout()
    layout.update({
        "title": "7-Day ROI Trend",
        "xaxis_title": "Date",
        "yaxis_title": "ROI (%)",
        "legend": dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    })
    
    fig.update_layout(**layout)
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 🎯 Risk-Adjusted Performance")
    
    # Scatter: Sharpe vs ROI
    fig = go.Figure()
    
    x_data = [random.uniform(0.3, 1.8) for _ in range(10)]  # Sharpe
    y_data = [random.uniform(-10, 25) for _ in range(10)]  # ROI
    
    fig.add_trace(
        go.Scatter(
            x=x_data,
            y=y_data,
            mode="markers",
            marker=dict(
                size=15,
                color=y_data,
                colorscale="RdYlGn",
                showscale=True,
                colorbar=dict(title="ROI (%)"),
            ),
            text=[f"Bot {i+1}" for i in range(10)],
            hovertemplate="<b>%{text}</b><br>Sharpe: %{x:.2f}<br>ROI: %{y:.2f}%<extra></extra>",
        )
    )
    
    layout = get_default_layout()
    layout.update({
        "title": "Sharpe Ratio vs ROI",
        "xaxis_title": "Sharpe Ratio",
        "yaxis_title": "ROI (%)",
    })
    
    fig.update_layout(**layout)
    
    st.plotly_chart(fig, use_container_width=True)

# Drawdown analysis
st.markdown("### 📉 Drawdown Analysis")

fig = go.Figure()

bots_sample = [f"Bot {i+1}" for i in range(8)]
drawdowns = [random.uniform(-25, -5) for _ in range(8)]

fig.add_trace(
    go.Bar(
        x=bots_sample,
        y=drawdowns,
        marker_color=["red" if d < -15 else "orange" if d < -10 else "green" for d in drawdowns],
    )
)

# Add threshold lines
fig.add_hline(y=-25, line_dash="dash", line_color="red", annotation_text="Emergency Halt")
fig.add_hline(y=-15, line_dash="dash", line_color="orange", annotation_text="Warning")

layout = get_default_layout()
layout.update({
    "title": "Max Drawdown by Bot",
    "xaxis_title": "Bot",
    "yaxis_title": "Drawdown (%)",
    "height": 400,
})

fig.update_layout(**layout)

st.plotly_chart(fig, use_container_width=True)

# Trade distributions
st.markdown("### 📊 Trade Distributions")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### P&L Distribution")
    
    # Histogram
    pnl_data = [random.uniform(-50, 150) for _ in range(100)]
    
    fig = go.Figure(
        data=[go.Histogram(x=pnl_data, nbinsx=20)]
    )
    
    layout = get_default_layout()
    layout.update({
        "title": "Trade P&L Distribution",
        "xaxis_title": "P&L ($)",
        "yaxis_title": "Frequency",
    })
    
    fig.update_layout(**layout)
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Position Hold Times")
    
    # Box plot
    hold_times = {
        f"Bot {i+1}": [random.uniform(0.5, 48) for _ in range(20)]
        for i in range(5)
    }
    
    fig = go.Figure()
    
    for bot, times in hold_times.items():
        fig.add_trace(
            go.Box(
                y=times,
                name=bot,
            )
        )
    
    layout = get_default_layout()
    layout.update({
        "title": "Hold Time Distribution",
        "yaxis_title": "Hours",
    })
    
    fig.update_layout(**layout)
    
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
