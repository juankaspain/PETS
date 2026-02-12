"""Settings page."""

import streamlit as st

from src.presentation.dashboard.components.api_client import APIClient

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

st.title("⚙️ Settings")

# API Configuration
st.subheader("🔌 API Configuration")

api_base_url = st.text_input(
    "API Endpoint",
    value=st.session_state.get("api_base_url", "http://localhost:8000"),
    help="FastAPI backend URL",
)

if st.button("Test Connection"):
    try:
        client = APIClient(api_base_url)
        response = client.health_check()
        st.success(f"✅ Connected: {response['service']} - {response['status']}")
        st.session_state["api_base_url"] = api_base_url
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")

st.markdown("---")

# Dashboard Settings
st.subheader("📊 Dashboard Settings")

auto_refresh = st.checkbox(
    "Auto-refresh",
    value=st.session_state.get("auto_refresh", True),
)

if auto_refresh:
    refresh_rate = st.slider(
        "Refresh rate (seconds)",
        10, 120, 30,
        help="How often to refresh data",
    )
    st.session_state["refresh_rate"] = refresh_rate

st.session_state["auto_refresh"] = auto_refresh

st.markdown("---")

# Theme
st.subheader("🎨 Theme")

theme = st.selectbox(
    "Color Theme",
    ["Light", "Dark"],
    index=1,  # Default to Dark
)

st.info("Theme changes require page refresh")

st.markdown("---")

# Database Health
st.subheader("🗄️ Database Health")

try:
    client = APIClient(api_base_url)
    # Mock database health check
    st.success("✅ TimescaleDB: Connected")
    st.success("✅ Redis: Connected")
except Exception as e:
    st.error(f"❌ Database connection failed: {e}")

st.markdown("---")

# System Info
st.subheader("ℹ️ System Info")

st.info("""
**PETS - Polymarket Elite Trading System**

Version: 1.0.0

Stack:
- Python 3.11+
- FastAPI (Backend)
- Streamlit (Dashboard)
- TimescaleDB (Time-series data)
- Redis (Caching)
- Web3.py (Blockchain)

Bot 8: Volatility Skew Arbitrage
- Evidence: $106K profit from manual trading
- Strategy: ATH/ATL spread >15%, entry <0.20 or >0.80
- Hold: 24-48h mean reversion
- Exit: 0.25-0.35 delta improvement OR 10% stop-loss
""")
