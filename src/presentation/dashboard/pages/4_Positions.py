"""Positions page - Active/closed positions tracking.

Real-time position monitoring with P&L tracking, zone heatmap,
and position detail modal with close capability.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from ..components.api_client import APIClient
from ..components.metric_card import create_metric_card
from ..components.websocket_client import WebSocketClient

# Page config
st.set_page_config(
    page_title="Positions - PETS Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title
st.title("💰 Positions")
st.markdown("Real-time position tracking with P&L analysis")

# Initialize clients
api_client = APIClient(base_url="http://localhost:8000", api_key="your-api-key-here")
ws_client = WebSocketClient(url="ws://localhost:8000/ws/positions")


def format_pnl(pnl: float) -> str:
    """Format P&L with color and sign."""
    if pnl > 0:
        return f"<span style='color: #22c55e;'>+${pnl:,.2f}</span>"
    elif pnl < 0:
        return f"<span style='color: #ef4444;'>-${abs(pnl):,.2f}</span>"
    else:
        return f"<span style='color: #6b7280;'>${pnl:,.2f}</span>"


def format_duration(seconds: int) -> str:
    """Format duration human-readable."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m"
    elif seconds < 86400:
        return f"{seconds // 3600}h {(seconds % 3600) // 60}m"
    else:
        return f"{seconds // 86400}d {(seconds % 86400) // 3600}h"


async def get_active_positions() -> List[Dict[str, Any]]:
    """Fetch active positions from API."""
    try:
        response = await api_client.get("/api/v1/positions", params={"status": "open"})
        return response.get("positions", [])
    except Exception as e:
        st.error(f"Error fetching active positions: {e}")
        return []


async def get_closed_positions(limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch closed positions from API."""
    try:
        response = await api_client.get(
            "/api/v1/positions", params={"status": "closed", "limit": limit}
        )
        return response.get("positions", [])
    except Exception as e:
        st.error(f"Error fetching closed positions: {e}")
        return []


async def close_position(position_id: str) -> bool:
    """Close position via API."""
    try:
        await api_client.post(f"/api/v1/positions/{position_id}/close")
        st.success(f"Position {position_id} closed successfully")
        return True
    except Exception as e:
        st.error(f"Error closing position: {e}")
        return False


def render_position_detail_modal(position: Dict[str, Any]) -> None:
    """Render position detail modal."""
    st.subheader(f"Position {position['position_id'][:8]}")

    # Entry info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Entry Price", f"${position['entry_price']:.3f}")
        st.caption(f"Opened: {position['opened_at']}")
    with col2:
        st.metric("Current Price", f"${position['current_price']:.3f}")
        st.caption(f"Market: {position['market_id'][:8]}...")
    with col3:
        unrealized_pnl = position.get("unrealized_pnl", 0.0)
        st.metric("Unrealized P&L", f"${unrealized_pnl:,.2f}", delta=f"{unrealized_pnl:,.2f}")

    # P&L breakdown
    st.markdown("**P&L Breakdown**")
    pnl_data = {
        "Type": ["Entry Cost", "Current Value", "Fees Paid", "Unrealized P&L"],
        "Amount": [
            position["entry_price"] * position["size"],
            position["current_price"] * position["size"],
            position.get("fees_paid", 0.0),
            unrealized_pnl,
        ],
    }
    st.dataframe(pd.DataFrame(pnl_data), use_container_width=True, hide_index=True)

    # Market context
    st.markdown("**Market Context**")
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"Liquidity: ${position.get('market_liquidity', 0):,.0f}")
    with col2:
        st.caption(f"Zone: {position.get('zone', 'N/A')}")

    # Close action
    st.markdown("---")
    if st.button("🛑 Close Position", type="primary", use_container_width=True):
        if st.session_state.get("confirm_close"):
            asyncio.run(close_position(position["position_id"]))
            st.session_state["confirm_close"] = False
            st.rerun()
        else:
            st.session_state["confirm_close"] = True
            st.warning("⚠️ Click again to confirm closing this position")


def render_active_positions_table(positions: List[Dict[str, Any]]) -> None:
    """Render active positions table."""
    if not positions:
        st.info("No active positions")
        return

    # Prepare data
    data = []
    for pos in positions:
        now = datetime.utcnow()
        opened = datetime.fromisoformat(pos["opened_at"].replace("Z", "+00:00"))
        duration_seconds = int((now - opened).total_seconds())

        data.append(
            {
                "Bot": pos["bot_id"],
                "Market": pos["market_id"][:12] + "...",
                "Side": pos["side"],
                "Size": f"{pos['size']:.2f}",
                "Entry": f"${pos['entry_price']:.3f}",
                "Current": f"${pos['current_price']:.3f}",
                "P&L": pos.get("unrealized_pnl", 0.0),
                "Duration": format_duration(duration_seconds),
                "Zone": pos.get("zone", "N/A"),
                "Status": "OPEN",
            }
        )

    df = pd.DataFrame(data)

    # Sort by P&L descending
    df = df.sort_values("P&L", ascending=False)

    # Color-code P&L
    def color_pnl(val: float) -> str:
        if val > 0:
            return "background-color: rgba(34, 197, 94, 0.2);"
        elif val < 0:
            return "background-color: rgba(239, 68, 68, 0.2);"
        return ""

    styled_df = df.style.applymap(color_pnl, subset=["P&L"])

    st.dataframe(styled_df, use_container_width=True, height=400, hide_index=True)

    # Click to view details
    st.caption("💡 Click on a row to view position details (coming soon)")


def render_closed_positions_history(positions: List[Dict[str, Any]]) -> None:
    """Render closed positions history."""
    if not positions:
        st.info("No closed positions")
        return

    # Metrics summary
    total_pnl = sum(pos.get("realized_pnl", 0.0) for pos in positions)
    avg_hold_time = sum(
        pos.get("hold_duration_seconds", 0) for pos in positions
    ) / len(positions)
    winners = sum(1 for pos in positions if pos.get("realized_pnl", 0.0) > 0)
    win_rate = (winners / len(positions)) * 100 if positions else 0.0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total P&L", f"${total_pnl:,.2f}")
    with col2:
        st.metric("Avg Hold Time", format_duration(int(avg_hold_time)))
    with col3:
        st.metric("Win Rate", f"{win_rate:.1f}%")
    with col4:
        st.metric("Total Closed", len(positions))

    # Table
    data = []
    for pos in positions:
        data.append(
            {
                "Closed": pos.get("closed_at", "N/A")[:16],
                "Bot": pos["bot_id"],
                "Market": pos["market_id"][:12] + "...",
                "Side": pos["side"],
                "Entry": f"${pos['entry_price']:.3f}",
                "Exit": f"${pos.get('exit_price', 0):.3f}",
                "P&L": pos.get("realized_pnl", 0.0),
                "Hold": format_duration(pos.get("hold_duration_seconds", 0)),
            }
        )

    df = pd.DataFrame(data)

    # Color-code P&L
    def color_pnl(val: float) -> str:
        if val > 0:
            return "background-color: rgba(34, 197, 94, 0.2);"
        elif val < 0:
            return "background-color: rgba(239, 68, 68, 0.2);"
        return ""

    styled_df = df.style.applymap(color_pnl, subset=["P&L"])

    st.dataframe(styled_df, use_container_width=True, height=300, hide_index=True)


def render_position_heatmap(positions: List[Dict[str, Any]]) -> None:
    """Render position heatmap (size vs P&L)."""
    if not positions:
        st.info("No positions to display")
        return

    # Prepare data
    data = {
        "Bot": [pos["bot_id"] for pos in positions],
        "Size": [pos["size"] for pos in positions],
        "P&L": [pos.get("unrealized_pnl", 0.0) for pos in positions],
        "Zone": [pos.get("zone", "N/A") for pos in positions],
        "Market": [pos["market_id"][:12] + "..." for pos in positions],
    }

    df = pd.DataFrame(data)

    # Bubble chart
    fig = px.scatter(
        df,
        x="Size",
        y="P&L",
        size="Size",
        color="Zone",
        hover_data=["Bot", "Market"],
        title="Position Heatmap: Size vs P&L",
        color_discrete_map={
            "ZONE_1": "#ef4444",
            "ZONE_2": "#f59e0b",
            "ZONE_3": "#10b981",
            "ZONE_4": "#3b82f6",
            "ZONE_5": "#8b5cf6",
        },
    )

    fig.update_layout(height=400, showlegend=True)

    st.plotly_chart(fig, use_container_width=True)


def render_portfolio_value_chart() -> None:
    """Render portfolio value evolution chart."""
    # Mock data (replace with API call)
    times = pd.date_range(end=datetime.utcnow(), periods=100, freq="5min")
    realized = [5000 + i * 10 + (i % 10) * 50 for i in range(100)]
    unrealized = [(i % 15) * 100 - 200 for i in range(100)]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=times, y=realized, fill="tozeroy", name="Realized P&L", line=dict(color="#10b981")
        )
    )

    fig.add_trace(
        go.Scatter(
            x=times,
            y=unrealized,
            fill="tonexty",
            name="Unrealized P&L",
            line=dict(color="#3b82f6"),
        )
    )

    fig.update_layout(
        title="Portfolio Value Evolution",
        xaxis_title="Time",
        yaxis_title="Value ($)",
        height=300,
        showlegend=True,
    )

    st.plotly_chart(fig, use_container_width=True)


# Main layout
tab1, tab2, tab3 = st.tabs(["📊 Active Positions", "📜 Closed History", "🗺️ Heatmap"])

with tab1:
    st.markdown("### Active Positions (Real-time)")

    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh (1s)", value=True)

    # Fetch active positions
    active_positions = asyncio.run(get_active_positions())

    # Positions table
    render_active_positions_table(active_positions)

    # Portfolio value chart
    st.markdown("---")
    render_portfolio_value_chart()

    # Auto-refresh
    if auto_refresh:
        import time

        time.sleep(1)
        st.rerun()

with tab2:
    st.markdown("### Closed Positions History")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_bot = st.selectbox("Filter by Bot", ["All", "bot-01", "bot-02", "bot-08"])
    with col2:
        filter_outcome = st.selectbox("Filter by Outcome", ["All", "Profit", "Loss"])
    with col3:
        date_range = st.selectbox("Date Range", ["Last 24h", "Last 7d", "Last 30d", "All"])

    # Fetch closed positions
    closed_positions = asyncio.run(get_closed_positions(limit=100))

    # Apply filters (simplified - would filter in API in production)
    filtered = closed_positions

    # Render history
    render_closed_positions_history(filtered)

    # Export button
    if st.button("📥 Export to CSV"):
        df = pd.DataFrame(filtered)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"closed_positions_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

with tab3:
    st.markdown("### Position Heatmap")
    st.caption("Bubble size = position size, color = zone, Y-axis = unrealized P&L")

    # Fetch active positions
    active_positions = asyncio.run(get_active_positions())

    # Render heatmap
    render_position_heatmap(active_positions)

# Footer
st.markdown("---")
st.caption("💰 Positions page | Auto-refresh: 1s | Last update: " + datetime.utcnow().strftime("%H:%M:%S"))
