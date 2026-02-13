"""Order Log page - Order execution tracking and analysis.

Real-time order monitoring with fill rates, latency analysis,
and rejection tracking.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..components.api_client import APIClient
from ..components.metric_card import create_metric_card

# Page config
st.set_page_config(
    page_title="Order Log - PETS Dashboard",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title
st.title("📜 Order Log")
st.markdown("Real-time order execution tracking and analysis")

# Initialize API client
api_client = APIClient(base_url="http://localhost:8000", api_key="your-api-key-here")


def get_status_badge(status: str) -> str:
    """Get colored badge for order status."""
    colors = {
        "FILLED": ("#22c55e", "✅"),
        "PARTIALLY_FILLED": ("#f59e0b", "🔶"),
        "PENDING": ("#3b82f6", "🔵"),
        "CANCELED": ("#6b7280", "⚪"),
        "REJECTED": ("#ef4444", "❌"),
        "EXPIRED": ("#9ca3af", "⏱️"),
    }
    color, emoji = colors.get(status, ("#6b7280", "●"))
    return f"<span style='color: {color}; font-weight: 600;'>{emoji} {status}</span>"


async def get_orders(
    bot_id: str | None = None,
    status: str | None = None,
    time_range: str = "24h",
    order_type: str | None = None,
) -> List[Dict[str, Any]]:
    """Fetch orders from API with filters."""
    try:
        params = {}
        if bot_id and bot_id != "All":
            params["bot_id"] = bot_id
        if status and status != "All":
            params["status"] = status
        if order_type and order_type != "All":
            params["order_type"] = order_type

        # Time range
        if time_range != "All":
            hours = {"1h": 1, "6h": 6, "24h": 24, "7d": 168}.get(time_range, 24)
            since = datetime.utcnow() - timedelta(hours=hours)
            params["since"] = since.isoformat()

        response = await api_client.get("/api/v1/orders", params=params)
        return response.get("orders", [])
    except Exception as e:
        st.error(f"Error fetching orders: {e}")
        return []


async def get_order_metrics(time_range: str = "24h") -> Dict[str, Any]:
    """Fetch order execution metrics."""
    try:
        params = {"time_range": time_range}
        response = await api_client.get("/api/v1/metrics/orders", params=params)
        return response
    except Exception as e:
        st.error(f"Error fetching order metrics: {e}")
        return {}


def render_order_detail_modal(order: Dict[str, Any]) -> None:
    """Render order detail modal."""
    st.subheader(f"Order {order['order_id'][:12]}...")

    # Order info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Bot", order["bot_id"])
    with col2:
        st.metric("Side", order["side"])
    with col3:
        st.metric("Type", order["order_type"])
    with col4:
        status_html = get_status_badge(order["status"])
        st.markdown(f"**Status:** {status_html}", unsafe_allow_html=True)

    # Execution timeline
    st.markdown("**Execution Timeline**")
    timeline_data = {
        "Event": ["Submitted", "Acknowledged", "Filled"],
        "Timestamp": [
            order.get("created_at", "N/A")[:19],
            order.get("acknowledged_at", "N/A")[:19] if order.get("acknowledged_at") else "N/A",
            order.get("filled_at", "N/A")[:19] if order.get("filled_at") else "Pending",
        ],
        "Latency": [
            "-",
            f"{order.get('ack_latency_ms', 0):.0f}ms" if order.get("ack_latency_ms") else "N/A",
            f"{order.get('fill_latency_ms', 0):.0f}ms" if order.get("fill_latency_ms") else "N/A",
        ],
    }
    st.dataframe(pd.DataFrame(timeline_data), use_container_width=True, hide_index=True)

    # Fill breakdown
    if order.get("fills"):
        st.markdown("**Fill Breakdown**")
        fills_data = []
        for fill in order["fills"]:
            fills_data.append(
                {
                    "Time": fill["timestamp"][:19],
                    "Size": fill["size"],
                    "Price": f"${fill['price']:.3f}",
                    "Fee": f"${fill['fee']:.2f}",
                }
            )
        st.dataframe(pd.DataFrame(fills_data), use_container_width=True, hide_index=True)

    # Rejection reason
    if order["status"] == "REJECTED" and order.get("rejection_reason"):
        st.error(f"❌ Rejection Reason: {order['rejection_reason']}")

    # Gas + Slippage
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"Gas Cost: ${order.get('gas_cost_usdc', 0):.2f}")
    with col2:
        st.caption(f"Slippage: {order.get('slippage_pct', 0):.2f}%")


def render_orders_table(orders: List[Dict[str, Any]]) -> None:
    """Render orders execution table."""
    if not orders:
        st.info("No orders found with current filters")
        return

    # Prepare data
    data = []
    for order in orders:
        fill_pct = (
            (order.get("filled_size", 0) / order["size"]) * 100 if order.get("filled_size") else 0.0
        )
        data.append(
            {
                "Time": order["created_at"][:16],
                "Bot": order["bot_id"],
                "Market": order["market_id"][:10] + "...",
                "Side": order["side"],
                "Type": order["order_type"],
                "Size": f"{order['size']:.2f}",
                "Price": f"${order['price']:.3f}",
                "Status": order["status"],
                "Fill%": f"{fill_pct:.0f}%",
                "Latency": f"{order.get('ack_latency_ms', 0):.0f}ms",
            }
        )

    df = pd.DataFrame(data)

    # Color-code status
    def color_status(val: str) -> str:
        if val == "FILLED":
            return "background-color: rgba(34, 197, 94, 0.2);"
        elif val == "REJECTED":
            return "background-color: rgba(239, 68, 68, 0.2);"
        elif val == "PARTIALLY_FILLED":
            return "background-color: rgba(245, 158, 11, 0.2);"
        return ""

    styled_df = df.style.applymap(color_status, subset=["Status"])

    st.dataframe(styled_df, use_container_width=True, height=400, hide_index=True)


def render_performance_metrics(metrics: Dict[str, Any]) -> None:
    """Render order performance metrics cards."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        fill_rate = metrics.get("fill_rate_pct", 0.0)
        create_metric_card("Fill Rate", f"{fill_rate:.1f}%", delta=None)

    with col2:
        avg_latency = metrics.get("avg_latency_ms", 0.0)
        create_metric_card("Avg Latency", f"{avg_latency:.0f}ms", delta=None)

    with col3:
        rejection_rate = metrics.get("rejection_rate_pct", 0.0)
        create_metric_card("Rejection Rate", f"{rejection_rate:.1f}%", delta=None)

    with col4:
        volume_24h = metrics.get("total_volume_usdc", 0.0)
        create_metric_card("24h Volume", f"${volume_24h:,.0f}", delta=None)


def render_latency_distribution(orders: List[Dict[str, Any]]) -> None:
    """Render latency distribution histogram."""
    if not orders:
        st.info("No data for latency distribution")
        return

    # Extract latencies
    latencies = [order.get("ack_latency_ms", 0) for order in orders if order.get("ack_latency_ms")]

    if not latencies:
        st.info("No latency data available")
        return

    # Create buckets
    buckets = ["0-50ms", "50-100ms", "100-200ms", ">200ms"]
    counts = [
        sum(1 for lat in latencies if lat < 50),
        sum(1 for lat in latencies if 50 <= lat < 100),
        sum(1 for lat in latencies if 100 <= lat < 200),
        sum(1 for lat in latencies if lat >= 200),
    ]

    fig = go.Figure(data=[go.Bar(x=buckets, y=counts, marker_color="#3b82f6")])

    # Target line at p99
    fig.add_hline(y=max(counts) * 0.99, line_dash="dash", line_color="#ef4444", annotation_text="p99 Target")

    fig.update_layout(
        title="Latency Distribution",
        xaxis_title="Latency Bucket",
        yaxis_title="Order Count",
        height=300,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_rejection_analysis(orders: List[Dict[str, Any]]) -> None:
    """Render rejection analysis charts."""
    rejected_orders = [o for o in orders if o["status"] == "REJECTED"]

    if not rejected_orders:
        st.info("No rejected orders in current time range")
        return

    col1, col2 = st.columns(2)

    with col1:
        # Rejection reasons pie chart
        reasons = {}
        for order in rejected_orders:
            reason = order.get("rejection_reason", "Unknown")
            reasons[reason] = reasons.get(reason, 0) + 1

        fig = px.pie(
            values=list(reasons.values()),
            names=list(reasons.keys()),
            title="Rejection Reasons",
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Rejections per bot bar chart
        bot_rejections = {}
        for order in rejected_orders:
            bot = order["bot_id"]
            bot_rejections[bot] = bot_rejections.get(bot, 0) + 1

        fig = go.Figure(data=[go.Bar(x=list(bot_rejections.keys()), y=list(bot_rejections.values()), marker_color="#ef4444")])
        fig.update_layout(title="Rejections by Bot", xaxis_title="Bot ID", yaxis_title="Count", height=300)
        st.plotly_chart(fig, use_container_width=True)


def render_trade_size_distribution(orders: List[Dict[str, Any]]) -> None:
    """Render trade size distribution."""
    filled_orders = [o for o in orders if o["status"] in ["FILLED", "PARTIALLY_FILLED"]]

    if not filled_orders:
        st.info("No filled orders to analyze")
        return

    sizes = [order["size"] for order in filled_orders]

    fig = px.histogram(x=sizes, nbins=20, title="Trade Size Distribution", labels={"x": "Order Size", "y": "Count"})
    fig.update_layout(height=300, showlegend=False)
    fig.update_traces(marker_color="#10b981")

    st.plotly_chart(fig, use_container_width=True)


# Main layout
st.markdown("### Order Execution Log")

# Filters
st.markdown("**Filters**")
col1, col2, col3, col4 = st.columns(4)

with col1:
    filter_bot = st.selectbox("Bot", ["All", "bot-01", "bot-02", "bot-05", "bot-08"])

with col2:
    filter_status = st.selectbox("Status", ["All", "FILLED", "PENDING", "CANCELED", "REJECTED"])

with col3:
    filter_time = st.selectbox("Time Range", ["1h", "6h", "24h", "7d", "All"])

with col4:
    filter_type = st.selectbox("Order Type", ["All", "POST_ONLY", "MARKET", "LIMIT"])

# Auto-refresh
auto_refresh = st.checkbox("Auto-refresh (2s)", value=True)

# Fetch data
orders = asyncio.run(get_orders(filter_bot, filter_status, filter_time, filter_type))
metrics = asyncio.run(get_order_metrics(filter_time))

# Performance metrics
st.markdown("---")
render_performance_metrics(metrics)

# Orders table
st.markdown("---")
st.markdown("**Execution Table**")
render_orders_table(orders)

# Export button
if st.button("📥 Export to CSV"):
    if orders:
        df = pd.DataFrame(orders)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"order_log_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
    else:
        st.warning("No orders to export")

# Analysis charts
st.markdown("---")
st.markdown("### Performance Analysis")

tab1, tab2, tab3 = st.tabs(["⏱️ Latency", "❌ Rejections", "📊 Trade Sizes"])

with tab1:
    render_latency_distribution(orders)

with tab2:
    render_rejection_analysis(orders)

with tab3:
    render_trade_size_distribution(orders)

# Auto-refresh
if auto_refresh:
    import time

    time.sleep(2)
    st.rerun()

# Footer
st.markdown("---")
st.caption("📜 Order Log | Auto-refresh: 2s | Last update: " + datetime.utcnow().strftime("%H:%M:%S"))
