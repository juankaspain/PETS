"""Risk Monitor page - Real-time risk tracking and circuit breakers.

Monitors zone exposure, circuit breakers, drawdowns, and risk alerts.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..components.api_client import APIClient
from ..components.metric_card import create_metric_card
from ..components.websocket_client import WebSocketClient

# Page config
st.set_page_config(
    page_title="Risk Monitor - PETS Dashboard",
    page_icon="⚠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title
st.title("⚠️ Risk Monitor")
st.markdown("Real-time risk tracking and circuit breaker monitoring")

# Initialize clients
api_client = APIClient(base_url="http://localhost:8000", api_key="your-api-key-here")
ws_client = WebSocketClient(url="ws://localhost:8000/ws/risk/alerts")


async def get_risk_metrics() -> Dict[str, Any]:
    """Fetch current risk metrics from API."""
    try:
        response = await api_client.get("/api/v1/risk/metrics")
        return response
    except Exception as e:
        st.error(f"Error fetching risk metrics: {e}")
        return {}


async def get_circuit_breakers() -> List[Dict[str, Any]]:
    """Fetch circuit breaker status."""
    try:
        response = await api_client.get("/api/v1/risk/circuit-breakers")
        return response.get("circuit_breakers", [])
    except Exception as e:
        st.error(f"Error fetching circuit breakers: {e}")
        return []


def render_zone_exposure_grid(metrics: Dict[str, Any]) -> None:
    """Render zone exposure grid with progress bars."""
    zone_exposure = metrics.get("zone_exposure", {})

    st.markdown("### Zone Exposure")

    zones = ["ZONE_1", "ZONE_2", "ZONE_3", "ZONE_4", "ZONE_5"]
    limits = [30, 40, 60, 20, 10]  # % limits per zone

    for i, (zone, limit) in enumerate(zip(zones, limits)):
        exposure = zone_exposure.get(zone, {}).get("exposure_pct", 0.0)
        exposed_capital = zone_exposure.get(zone, {}).get("exposed_capital_usdc", 0.0)

        # Color based on utilization
        if exposure < limit * 0.7:
            color = "#22c55e"  # Green - safe
            status = "✅ Safe"
        elif exposure < limit * 0.9:
            color = "#f59e0b"  # Yellow - warning
            status = "⚠️ Warning"
        else:
            color = "#ef4444"  # Red - danger
            status = "🛑 Danger"

        col1, col2, col3 = st.columns([2, 3, 1])

        with col1:
            st.markdown(f"**{zone}**")
            st.caption(f"Limit: {limit}%")

        with col2:
            st.progress(min(exposure / limit, 1.0))
            st.caption(f"${exposed_capital:,.0f} ({exposure:.1f}% / {limit}%)")

        with col3:
            st.markdown(f"<span style='color: {color};'>{status}</span>", unsafe_allow_html=True)


def render_circuit_breakers(circuit_breakers: List[Dict[str, Any]]) -> None:
    """Render circuit breaker status cards."""
    st.markdown("### Circuit Breakers")

    breaker_configs = [
        {"name": "3 Consecutive Losses", "key": "consecutive_losses", "threshold": 3},
        {"name": "5% Daily Loss", "key": "daily_loss", "threshold": 5.0},
        {"name": "25% Bot Drawdown", "key": "bot_drawdown", "threshold": 25.0},
        {"name": "40% Portfolio Drawdown", "key": "portfolio_drawdown", "threshold": 40.0},
    ]

    cols = st.columns(4)

    for i, (col, config) in enumerate(zip(cols, breaker_configs)):
        with col:
            # Find breaker in response
            breaker = next(
                (b for b in circuit_breakers if b["breaker_type"] == config["key"]), None
            )

            if breaker:
                status = breaker.get("status", "ARMED")
                current_value = breaker.get("current_value", 0.0)
                triggered_at = breaker.get("triggered_at")

                if status == "TRIGGERED":
                    st.error(f"🛑 {config['name']}")
                    st.caption(f"Triggered: {triggered_at[:16] if triggered_at else 'N/A'}")
                    st.caption(f"Value: {current_value:.1f} / {config['threshold']}")
                else:
                    st.success(f"✅ {config['name']}")
                    st.caption(f"Status: {status}")
                    st.caption(f"Value: {current_value:.1f} / {config['threshold']}")
            else:
                st.info(f"🔵 {config['name']}")
                st.caption("No data available")


def render_drawdown_gauges(metrics: Dict[str, Any]) -> None:
    """Render drawdown gauge charts."""
    st.markdown("### Drawdown Monitoring")

    col1, col2 = st.columns(2)

    with col1:
        # Portfolio drawdown
        portfolio_dd = metrics.get("portfolio_drawdown_pct", 0.0)

        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=portfolio_dd,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "Portfolio Drawdown %"},
                delta={"reference": 40.0},
                gauge={
                    "axis": {"range": [None, 50]},
                    "bar": {"color": "#3b82f6"},
                    "steps": [
                        {"range": [0, 20], "color": "#22c55e"},
                        {"range": [20, 35], "color": "#f59e0b"},
                        {"range": [35, 50], "color": "#ef4444"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": 40,
                    },
                },
            )
        )

        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Bot max drawdown
        bot_drawdowns = metrics.get("bot_drawdowns", {})
        max_bot_dd = max(bot_drawdowns.values()) if bot_drawdowns else 0.0
        max_bot_id = (
            max(bot_drawdowns, key=bot_drawdowns.get) if bot_drawdowns else "N/A"
        )

        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=max_bot_dd,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": f"Max Bot Drawdown % ({max_bot_id})"},
                delta={"reference": 25.0},
                gauge={
                    "axis": {"range": [None, 40]},
                    "bar": {"color": "#3b82f6"},
                    "steps": [
                        {"range": [0, 15], "color": "#22c55e"},
                        {"range": [15, 22], "color": "#f59e0b"},
                        {"range": [22, 40], "color": "#ef4444"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": 25,
                    },
                },
            )
        )

        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)


def render_consecutive_loss_tracker(metrics: Dict[str, Any]) -> None:
    """Render consecutive loss tracker per bot."""
    st.markdown("### Consecutive Loss Tracker")

    consecutive_losses = metrics.get("consecutive_losses_per_bot", {})

    if not consecutive_losses:
        st.info("No consecutive loss data available")
        return

    data = []
    for bot_id, count in consecutive_losses.items():
        status = "✅ Safe" if count < 2 else "⚠️ Warning" if count < 3 else "🛑 HALT"
        color = "#22c55e" if count < 2 else "#f59e0b" if count < 3 else "#ef4444"

        data.append({"Bot": bot_id, "Consecutive Losses": count, "Status": status, "Color": color})

    df = pd.DataFrame(data)

    # Display as table
    for _, row in df.iterrows():
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            st.markdown(f"**{row['Bot']}**")
        with col2:
            st.progress(min(row["Consecutive Losses"] / 3.0, 1.0))
            st.caption(f"{row['Consecutive Losses']} / 3")
        with col3:
            st.markdown(
                f"<span style='color: {row['Color']};'>{row['Status']}</span>",
                unsafe_allow_html=True,
            )


def render_risk_alerts_feed() -> None:
    """Render real-time risk alerts feed."""
    st.markdown("### Risk Alerts Feed")

    # Mock alerts (replace with WebSocket stream)
    alerts = [
        {
            "timestamp": "2026-02-13 01:45:23",
            "severity": "WARNING",
            "type": "ZONE_VIOLATION",
            "message": "Bot-08: Zone 4 exposure 22% exceeds 20% limit",
        },
        {
            "timestamp": "2026-02-13 01:40:15",
            "severity": "INFO",
            "type": "DRAWDOWN_WARNING",
            "message": "Bot-05: Drawdown reached 18%",
        },
        {
            "timestamp": "2026-02-13 01:35:08",
            "severity": "CRITICAL",
            "type": "CIRCUIT_BREAKER",
            "message": "Bot-02: 3 consecutive losses - PAUSED",
        },
    ]

    # Filter
    severity_filter = st.multiselect(
        "Filter by Severity", ["INFO", "WARNING", "CRITICAL"], default=["INFO", "WARNING", "CRITICAL"]
    )

    filtered_alerts = [a for a in alerts if a["severity"] in severity_filter]

    # Display alerts
    for alert in filtered_alerts:
        severity = alert["severity"]
        color = (
            "#3b82f6" if severity == "INFO" else "#f59e0b" if severity == "WARNING" else "#ef4444"
        )
        emoji = "🔵" if severity == "INFO" else "⚠️" if severity == "WARNING" else "🛑"

        st.markdown(
            f"<div style='padding: 10px; border-left: 4px solid {color}; margin-bottom: 10px; background-color: rgba(255,255,255,0.05);'>"
            f"<small style='color: #9ca3af;'>{alert['timestamp']}</small><br>"
            f"<span style='color: {color}; font-weight: 600;'>{emoji} {alert['severity']}</span> - {alert['type']}<br>"
            f"{alert['message']}"
            f"</div>",
            unsafe_allow_html=True,
        )


# Main layout
col1, col2 = st.columns([2, 1])

with col1:
    # Fetch metrics
    metrics = asyncio.run(get_risk_metrics())

    # Zone exposure
    render_zone_exposure_grid(metrics)

    st.markdown("---")

    # Drawdown gauges
    render_drawdown_gauges(metrics)

with col2:
    # Circuit breakers
    circuit_breakers = asyncio.run(get_circuit_breakers())
    render_circuit_breakers(circuit_breakers)

    st.markdown("---")

    # Consecutive loss tracker
    render_consecutive_loss_tracker(metrics)

# Risk alerts feed
st.markdown("---")
render_risk_alerts_feed()

# Auto-refresh
auto_refresh = st.checkbox("Auto-refresh (1s)", value=True)

if auto_refresh:
    import time

    time.sleep(1)
    st.rerun()

# Footer
st.markdown("---")
st.caption(
    "⚠️ Risk Monitor | Auto-refresh: 1s | Last update: "
    + datetime.utcnow().strftime("%H:%M:%S")
)
