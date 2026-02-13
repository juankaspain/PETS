"""Risk Monitor page.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import asyncio

import streamlit as st

from src.presentation.dashboard.api_client import APIClient
from src.presentation.dashboard.utils import format_currency, format_percentage

st.set_page_config(page_title="Risk Monitor", page_icon="⚠️", layout="wide")

st.title("⚠️ Risk Monitor")

# Initialize API client
if "api_client" not in st.session_state:
    st.session_state.api_client = APIClient()

api_client = st.session_state.api_client


async def load_risk_metrics():
    """Load risk metrics."""
    try:
        return await api_client.get_risk_metrics()
    except Exception as e:
        st.error(f"Error loading risk metrics: {e}")
        return {}


risk_metrics = asyncio.run(load_risk_metrics())

# Risk metrics
st.subheader("Portfolio Risk Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Max Drawdown",
        format_percentage(risk_metrics.get("max_drawdown", 0)),
    )

with col2:
    st.metric(
        "Current Drawdown",
        format_percentage(risk_metrics.get("current_drawdown", 0)),
    )

with col3:
    st.metric(
        "Open Exposure",
        format_currency(risk_metrics.get("open_exposure", 0)),
    )

with col4:
    st.metric(
        "Consecutive Losses",
        risk_metrics.get("consecutive_losses", 0),
    )

st.divider()

# Circuit breakers
st.subheader("Circuit Breakers")


async def load_circuit_breakers():
    """Load circuit breaker statuses."""
    try:
        return await api_client.get_circuit_breakers()
    except Exception as e:
        st.error(f"Error loading circuit breakers: {e}")
        return {}


circuit_breakers = asyncio.run(load_circuit_breakers())

col1, col2, col3, col4 = st.columns(4)

with col1:
    status = circuit_breakers.get("consecutive_losses", {}).get("status", "OK")
    st.metric(
        "3 Consecutive Losses",
        status,
        delta="OPEN" if status != "OK" else None,
        delta_color="inverse",
    )

with col2:
    status = circuit_breakers.get("daily_loss", {}).get("status", "OK")
    st.metric(
        "5% Daily Loss",
        status,
        delta="OPEN" if status != "OK" else None,
        delta_color="inverse",
    )

with col3:
    status = circuit_breakers.get("bot_drawdown", {}).get("status", "OK")
    st.metric(
        "25% Bot Drawdown",
        status,
        delta="OPEN" if status != "OK" else None,
        delta_color="inverse",
    )

with col4:
    status = circuit_breakers.get("portfolio_drawdown", {}).get("status", "OK")
    st.metric(
        "40% Portfolio Drawdown",
        status,
        delta="OPEN" if status != "OK" else None,
        delta_color="inverse",
    )

st.divider()

# Emergency halt
st.subheader("Emergency Controls")

if st.button("🚨 EMERGENCY HALT ALL BOTS", type="primary"):
    if st.button("Confirm Emergency Halt"):
        asyncio.run(api_client.emergency_halt())
        st.success("Emergency halt triggered!")
        st.rerun()
