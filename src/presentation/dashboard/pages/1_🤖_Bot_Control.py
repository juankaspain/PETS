"""Bot Control page.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import asyncio

import streamlit as st

from src.presentation.dashboard.api_client import APIClient
from src.presentation.dashboard.components.status_badge import bot_status_badge
from src.presentation.dashboard.utils import format_currency, format_percentage

st.set_page_config(page_title="Bot Control", page_icon="🤖", layout="wide")

st.title("🤖 Bot Control")

# Initialize API client
if "api_client" not in st.session_state:
    st.session_state.api_client = APIClient()

api_client = st.session_state.api_client


async def load_bots():
    """Load bots list."""
    try:
        result = await api_client.list_bots()
        return result.get("bots", [])
    except Exception as e:
        st.error(f"Error loading bots: {e}")
        return []


# Load bots
bots = asyncio.run(load_bots())

if not bots:
    st.info("No bots configured yet.")
else:
    # Bot grid
    cols = st.columns(4)
    
    for idx, bot in enumerate(bots):
        with cols[idx % 4]:
            with st.container(border=True):
                st.subheader(f"Bot {bot.get('bot_id', 'N/A')}")
                st.write(f"**Strategy**: {bot.get('strategy_type', 'N/A')}")
                
                # Status badge
                bot_status_badge(bot.get("state", "IDLE"))
                
                # Metrics
                st.metric(
                    "Capital",
                    format_currency(bot.get("capital_allocated", 0)),
                )
                st.metric(
                    "P&L",
                    format_currency(bot.get("total_pnl", 0)),
                    delta=format_percentage(bot.get("roi", 0)),
                )
                
                # Actions
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("▶️", key=f"start_{bot['bot_id']}"):
                        asyncio.run(api_client.start_bot(bot["bot_id"]))
                        st.rerun()
                
                with col2:
                    if st.button("⏸️", key=f"pause_{bot['bot_id']}"):
                        asyncio.run(api_client.pause_bot(bot["bot_id"]))
                        st.rerun()
                
                with col3:
                    if st.button("⏹️", key=f"stop_{bot['bot_id']}"):
                        asyncio.run(api_client.stop_bot(bot["bot_id"]))
                        st.rerun()

st.divider()

# Selected bot detail
if bots:
    selected_bot_id = st.selectbox(
        "Select bot for details",
        [bot["bot_id"] for bot in bots],
    )
    
    if selected_bot_id:
        async def load_bot_details():
            """Load bot details."""
            try:
                return await api_client.get_bot(selected_bot_id)
            except Exception as e:
                st.error(f"Error loading bot details: {e}")
                return None
        
        bot_details = asyncio.run(load_bot_details())
        
        if bot_details:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Configuration")
                st.json(bot_details.get("config", {}))
            
            with col2:
                st.subheader("Metrics")
                async def load_metrics():
                    try:
                        return await api_client.get_bot_metrics(selected_bot_id)
                    except Exception:
                        return {}
                
                metrics = asyncio.run(load_metrics())
                
                st.metric("Win Rate", format_percentage(metrics.get("win_rate", 0)))
                st.metric("Avg P&L", format_currency(metrics.get("avg_pnl", 0)))
                st.metric("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.2f}")
