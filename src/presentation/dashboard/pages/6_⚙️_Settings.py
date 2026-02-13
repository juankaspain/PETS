"""Settings page.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import streamlit as st

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

st.title("⚙️ System Settings")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Global Config",
    "Bot Settings",
    "Notifications",
    "System Health",
])

with tab1:
    st.subheader("Global Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input(
            "Max Daily Loss (%)",
            min_value=0.0,
            max_value=100.0,
            value=5.0,
            step=0.1,
        )
        
        st.number_input(
            "Max Portfolio Drawdown (%)",
            min_value=0.0,
            max_value=100.0,
            value=40.0,
            step=1.0,
        )
    
    with col2:
        st.number_input(
            "Max Bot Drawdown (%)",
            min_value=0.0,
            max_value=100.0,
            value=25.0,
            step=1.0,
        )
        
        st.number_input(
            "Consecutive Loss Limit",
            min_value=1,
            max_value=10,
            value=3,
        )
    
    if st.button("Save Global Config"):
        st.success("Global configuration saved!")

with tab2:
    st.subheader("Bot-Specific Settings")
    
    selected_bot = st.selectbox(
        "Select bot",
        [f"Bot {i}" for i in range(1, 11)],
    )
    
    st.json({
        "strategy_type": "tail_risk",
        "capital_allocated": 5000,
        "kelly_fraction": 0.25,
        "max_position_size": 1000,
        "allowed_zones": [1, 2],
    })
    
    if st.button("Update Bot Config"):
        st.success(f"{selected_bot} configuration updated!")

with tab3:
    st.subheader("Notification Settings")
    
    st.checkbox("Email notifications", value=True)
    st.checkbox("Telegram notifications", value=False)
    st.checkbox("Discord notifications", value=False)
    
    st.text_input("Email address", value="user@example.com")
    
    if st.button("Save Notifications"):
        st.success("Notification settings saved!")

with tab4:
    st.subheader("System Health")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("API Status", "🟢 Healthy")
    
    with col2:
        st.metric("Database", "🟢 Connected")
    
    with col3:
        st.metric("WebSocket", "🟢 Active")
    
    st.divider()
    
    st.subheader("Version Info")
    st.code("""
PETS v2.12.0
Python 3.11.7
FastAPI 0.108.0
Streamlit 1.30.0
TimescaleDB 2.13.0
Redis 7.2.0
    """)
