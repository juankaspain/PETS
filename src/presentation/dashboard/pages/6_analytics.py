"""Analytics page."""

import streamlit as st

from src.presentation.dashboard.components.api_client import APIClient
from src.presentation.dashboard.components.charts import (
    create_equity_curve,
    create_pnl_chart,
)

st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")

st.title("📈 Analytics")

# API client
api_base_url = st.session_state.get("api_base_url", "http://localhost:8000")
client = APIClient(api_base_url)

# Fetch metrics
try:
    performance = client.get_performance_metrics()
    portfolio = client.get_portfolio_metrics()
except Exception as e:
    st.error(f"Failed to fetch analytics: {e}")
    st.stop()

# Performance Metrics
st.subheader("📊 Performance Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Trades", performance["total_trades"])

with col2:
    st.metric(
        "Win Rate",
        f"{performance['win_rate']*100:.1f}%",
        delta=f"{performance['winning_trades']}W / {performance['losing_trades']}L",
    )

with col3:
    st.metric("Profit Factor", f"{performance['profit_factor']:.2f}")

with col4:
    sharpe = performance.get('sharpe_ratio')
    st.metric(
        "Sharpe Ratio",
        f"{sharpe:.2f}" if sharpe else "N/A",
    )

st.markdown("---")

# Charts
st.subheader("📈 Equity Curve")

# Mock data for equity curve (real implementation would fetch from DB)
equity_data = [
    {"date": "2025-02-01", "value": 10000},
    {"date": "2025-02-02", "value": 10150},
    {"date": "2025-02-03", "value": 10200},
    {"date": "2025-02-04", "value": 10180},
    {"date": "2025-02-05", "value": 10350},
    {"date": "2025-02-06", "value": 10500},
]

fig = create_equity_curve(equity_data)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# P&L Chart
st.subheader("💰 Daily P&L")

# Mock data for daily P&L
pnl_data = [
    {"date": "2025-02-01", "pnl": 50},
    {"date": "2025-02-02", "pnl": 150},
    {"date": "2025-02-03", "pnl": 50},
    {"date": "2025-02-04", "pnl": -20},
    {"date": "2025-02-05", "pnl": 170},
    {"date": "2025-02-06", "pnl": 150},
]

fig = create_pnl_chart(pnl_data)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Trade Analysis
st.subheader("📊 Trade Analysis")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Average Win",
        f"${performance['avg_win']:,.2f}",
    )
    st.metric(
        "Max Drawdown",
        f"{performance['max_drawdown_pct']:.2f}%",
    )

with col2:
    st.metric(
        "Average Loss",
        f"${performance['avg_loss']:,.2f}",
    )
    st.metric(
        "Current Drawdown",
        f"{performance['current_drawdown_pct']:.2f}%",
    )
