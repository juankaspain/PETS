"""Bot Management page."""

import streamlit as st

from src.presentation.dashboard.components.api_client import APIClient

st.set_page_config(page_title="Bot Management", page_icon="🤖", layout="wide")

st.title("🤖 Bot Management")

# API client
api_base_url = st.session_state.get("api_base_url", "http://localhost:8000")
client = APIClient(api_base_url)

# Fetch bots
try:
    bots = client.list_bots()
except Exception as e:
    st.error(f"Failed to fetch bots: {e}")
    bots = []

# Create new bot
with st.expander("➕ Create New Bot", expanded=False):
    st.subheader("Bot 8: Volatility Skew Arbitrage")
    
    with st.form("create_bot"):
        capital = st.number_input(
            "Capital Allocated",
            min_value=1000,
            max_value=100000,
            value=10000,
            step=1000,
            help="Capital allocated to this bot",
        )
        
        st.markdown("**Strategy Configuration:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            spread_threshold = st.slider(
                "Spread Threshold",
                0.10, 0.30, 0.15,
                step=0.01,
                help="Minimum ATH/ATL spread to trigger entry",
            )
            
            entry_low = st.slider(
                "Entry Threshold (Low)",
                0.05, 0.30, 0.20,
                step=0.01,
                help="Buy when YES price below this",
            )
        
        with col2:
            hold_min = st.slider(
                "Hold Hours (Min)",
                12, 48, 24,
                step=6,
                help="Minimum holding period",
            )
            
            hold_max = st.slider(
                "Hold Hours (Max)",
                24, 96, 48,
                step=6,
                help="Maximum holding period",
            )
        
        submitted = st.form_submit_button("Create Bot")
        
        if submitted:
            try:
                config = {
                    "spread_threshold": spread_threshold,
                    "entry_threshold_low": entry_low,
                    "entry_threshold_high": 1.0 - entry_low,
                    "hold_hours_min": hold_min,
                    "hold_hours_max": hold_max,
                    "target_delta": 0.30,
                    "stop_loss_pct": 0.10,
                }
                
                response = client.create_bot(
                    strategy_type="VOLATILITY_SKEW",
                    config=config,
                    capital_allocated=capital,
                )
                
                st.success(f"Bot {response['bot_id']} created successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to create bot: {e}")

st.markdown("---")

# Existing bots
st.subheader("Existing Bots")

if bots:
    for bot in bots:
        with st.expander(f"Bot {bot['bot_id']} - {bot['strategy_type']} ({bot['state']})"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("State", bot["state"])
                st.metric("Capital", f"${bot['capital_allocated']:,.0f}")
            
            with col2:
                st.json(bot["config"])
            
            with col3:
                # Control buttons
                if bot["state"] in ["IDLE", "STOPPED"]:
                    if st.button(f"▶️ Start Bot {bot['bot_id']}", key=f"start_{bot['bot_id']}"):
                        try:
                            client.update_bot_state(bot["bot_id"], "ANALYZING")
                            st.success(f"Bot {bot['bot_id']} started")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to start bot: {e}")
                
                elif bot["state"] not in ["ERROR"]:
                    if st.button(f"⏸️ Stop Bot {bot['bot_id']}", key=f"stop_{bot['bot_id']}"):
                        try:
                            client.update_bot_state(bot["bot_id"], "STOPPED")
                            st.success(f"Bot {bot['bot_id']} stopped")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to stop bot: {e}")
                
                if st.button(f"🗑️ Delete Bot {bot['bot_id']}", key=f"delete_{bot['bot_id']}"):
                    try:
                        client.delete_bot(bot["bot_id"])
                        st.success(f"Bot {bot['bot_id']} deleted")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to delete bot: {e}")
else:
    st.info("No bots created yet. Create your first Bot 8!")
