"""Risk page."""

import streamlit as st

from src.presentation.dashboard.components.api_client import APIClient
from src.presentation.dashboard.components.charts import create_zone_exposure_chart

st.set_page_config(page_title="Risk", page_icon="⚠️", layout="wide")

st.title("⚠️ Risk Management")

# API client
api_base_url = st.session_state.get("api_base_url", "http://localhost:8000")
client = APIClient(api_base_url)

# Fetch risk metrics
try:
    risk = client.get_risk_metrics()
    portfolio = client.get_portfolio_metrics()
except Exception as e:
    st.error(f"Failed to fetch risk metrics: {e}")
    st.stop()

# Risk Metrics
st.subheader("📊 Risk Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("VaR (95%)", f"${risk['var_95']:,.2f}")

with col2:
    st.metric("VaR (99%)", f"${risk['var_99']:,.2f}")

with col3:
    st.metric("Max Position", f"{risk['max_position_size_pct']}%")

with col4:
    st.metric("Leverage", f"{risk['current_leverage']:.2f}x")

st.markdown("---")

# Circuit Breakers
st.subheader("🚨 Circuit Breakers")

cb = risk["circuit_breaker_status"]

col1, col2, col3, col4 = st.columns(4)

with col1:
    consecutive_losses = cb.get("consecutive_losses", 0)
    status = "🔴 TRIGGERED" if consecutive_losses >= 3 else "🟢 OK"
    st.metric(
        "Consecutive Losses",
        f"{consecutive_losses} / 3",
        delta=status,
    )

with col2:
    daily_loss = cb.get("daily_loss_triggered", False)
    status = "🔴 TRIGGERED" if daily_loss else "🟢 OK"
    st.metric(
        "Daily Loss (5%)",
        status,
    )

with col3:
    bot_dd = cb.get("bot_drawdown_triggered", False)
    status = "🔴 TRIGGERED" if bot_dd else "🟢 OK"
    st.metric(
        "Bot Drawdown (25%)",
        status,
    )

with col4:
    portfolio_dd = cb.get("portfolio_drawdown_triggered", False)
    status = "🔴 TRIGGERED" if portfolio_dd else "🟢 OK"
    st.metric(
        "Portfolio Drawdown (40%)",
        status,
    )

st.markdown("---")

# Zone Exposure
st.subheader("📍 Zone Exposure")

zone_exposure = risk.get("zone_exposure", {})

if zone_exposure:
    fig = create_zone_exposure_chart(zone_exposure)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No zone exposure data")

st.markdown("---")

# Position Risk Table
st.subheader("💼 Position Risk")

try:
    positions = client.list_positions(status="open")
except Exception as e:
    st.error(f"Failed to fetch positions: {e}")
    positions = []

if positions:
    st.dataframe(
        [
            {
                "Market": pos["market_id"][:12] + "...",
                "Size": f"${pos['size']:,.0f}",
                "% Portfolio": f"{(pos['size']/portfolio['total_value']*100):.2f}%",
                "Zone": f"Z{pos['zone']}",
                "Risk Level": "🟢 Low" if pos['zone'] <= 2 else "🟡 Medium" if pos['zone'] == 3 else "🔴 High",
            }
            for pos in positions
        ],
        use_container_width=True,
    )
else:
    st.info("No open positions")
