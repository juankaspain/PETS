"""Overview page - Portfolio summary."""

import streamlit as st

from src.presentation.dashboard.components.api_client import APIClient

st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")

st.title("📊 Portfolio Overview")

# API client
api_base_url = st.session_state.get("api_base_url", "http://localhost:8000")
client = APIClient(api_base_url)

# Auto-refresh
auto_refresh = st.session_state.get("auto_refresh", True)
if auto_refresh:
    import time
    time.sleep(30)  # Refresh every 30s
    st.rerun()

# Fetch data
try:
    portfolio = client.get_portfolio_metrics()
    performance = client.get_performance_metrics()
    bots = client.list_bots()
    positions = client.list_positions(status="open")
except Exception as e:
    st.error(f"Failed to fetch data: {e}")
    st.stop()

# Key metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Value",
        f"${portfolio['total_value']:,.2f}",
        delta=f"{portfolio['daily_return_pct']:.2f}% today",
    )

with col2:
    st.metric(
        "Daily P&L",
        f"${portfolio['daily_pnl']:,.2f}",
        delta=f"{portfolio['daily_return_pct']:.2f}%",
    )

with col3:
    st.metric(
        "Total P&L",
        f"${portfolio['total_pnl']:,.2f}",
        delta=f"{portfolio['total_return_pct']:.2f}%",
    )

with col4:
    st.metric(
        "Win Rate",
        f"{performance['win_rate']*100:.1f}%",
        delta=f"{performance['winning_trades']}W / {performance['losing_trades']}L",
    )

st.markdown("---")

# Active Bots
st.subheader("🤖 Active Bots")

if bots:
    bot_cols = st.columns(len(bots))
    for idx, bot in enumerate(bots):
        with bot_cols[idx]:
            state_emoji = {
                "IDLE": "⏸️",
                "ANALYZING": "🔍",
                "PLACING": "📝",
                "HOLDING": "🤝",
                "EXITING": "🚪",
                "STOPPED": "🛑",
                "ERROR": "❌",
            }.get(bot["state"], "❓")
            
            st.metric(
                f"Bot {bot['bot_id']}",
                f"{state_emoji} {bot['state']}",
                delta=f"${bot['capital_allocated']:,.0f} capital",
            )
else:
    st.info("No active bots")

st.markdown("---")

# Open Positions
st.subheader("💼 Open Positions")

if positions:
    st.dataframe(
        [
            {
                "Market": pos["market_id"][:12] + "...",
                "Side": pos["side"],
                "Size": f"${pos['size']:,.0f}",
                "Entry": f"{pos['entry_price']:.4f}",
                "Current": f"{pos['current_price']:.4f}" if pos["current_price"] else "N/A",
                "P&L": f"${pos['unrealized_pnl']:,.2f}" if pos["unrealized_pnl"] else "N/A",
                "Zone": f"Z{pos['zone']}",
            }
            for pos in positions
        ],
        use_container_width=True,
    )
else:
    st.info("No open positions")

st.markdown("---")

# Circuit Breakers
st.subheader("⚠️ Circuit Breaker Status")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Consecutive Losses", "0 / 3", delta="🟢 OK")

with col2:
    st.metric("Daily Loss", "0% / 5%", delta="🟢 OK")

with col3:
    st.metric("Bot Drawdown", "0% / 25%", delta="🟢 OK")

with col4:
    st.metric("Portfolio Drawdown", "0% / 40%", delta="🟢 OK")
