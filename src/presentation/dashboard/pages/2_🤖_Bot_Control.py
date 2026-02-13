"""Bot Control dashboard page.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import streamlit as st
import time
from datetime import datetime
import random

from src.presentation.dashboard.components import (
    APIClient,
    StateManager,
)
from src.presentation.dashboard.components.chart_utils import create_line_chart

# Page config
st.set_page_config(
    page_title="Bot Control - PETS Dashboard",
    page_icon="🤖",
    layout="wide",
)

# Initialize state
state = StateManager()

if not state.has("api_client"):
    state.set("api_client", APIClient(base_url="http://localhost:8000"))

api_client = state.get("api_client")

# Header
st.title("🤖 Bot Control Center")

# Bot selection
st.markdown("### Select Bot")

bots = api_client.get_bot_list()

if not bots:
    # Generate sample bots if API unavailable
    bots = [
        {"bot_id": i+1, "strategy_type": f"Strategy_{i+1}", "state": "ACTIVE"}
        for i in range(10)
    ]

col1, col2 = st.columns([3, 1])

with col1:
    # Bot grid
    bot_cols = st.columns(5)
    
    selected_bot_id = state.get("selected_bot_id", 1)
    
    for i, bot in enumerate(bots[:10]):
        with bot_cols[i % 5]:
            bot_id = bot.get("bot_id", i+1)
            state_emoji = {
                "ACTIVE": "🟢",
                "PAUSED": "🟡",
                "STOPPED": "🔴",
                "ERROR": "⚠️",
            }.get(bot.get("state", "STOPPED"), "⚪")
            
            if st.button(
                f"{state_emoji} Bot {bot_id}",
                key=f"bot_select_{bot_id}",
                use_container_width=True,
            ):
                state.set("selected_bot_id", bot_id)
                st.rerun()

with col2:
    st.markdown("**Legend**")
    st.caption("🟢 Active")
    st.caption("🟡 Paused")
    st.caption("🔴 Stopped")
    st.caption("⚠️ Error")

st.markdown("---")

# Selected bot details
selected_bot_id = state.get("selected_bot_id", 1)
st.markdown(f"### Bot {selected_bot_id} Details")

# Fetch bot metrics
bot_metrics = api_client.get_bot_metrics(selected_bot_id)

if not bot_metrics:
    # Sample data
    bot_metrics = {
        "bot_id": selected_bot_id,
        "state": "ACTIVE",
        "strategy_type": f"Strategy_{selected_bot_id}",
        "pnl": random.uniform(-100, 500),
        "open_positions": random.randint(0, 5),
        "win_rate": random.uniform(45, 65),
        "sharpe_ratio": random.uniform(0.5, 1.5),
    }

# Metrics cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Status", bot_metrics.get("state", "UNKNOWN"))

with col2:
    pnl = bot_metrics.get("pnl", 0)
    st.metric("P&L", f"${pnl:+,.2f}")

with col3:
    st.metric("Open Positions", bot_metrics.get("open_positions", 0))

with col4:
    st.metric(
        "Win Rate",
        f"{bot_metrics.get('win_rate', 0):.1f}%",
        f"Sharpe: {bot_metrics.get('sharpe_ratio', 0):.2f}",
    )

st.markdown("---")

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["📊 Metrics", "⚙️ Config", "🎬 Actions", "📜 Logs"])

with tab1:
    st.markdown("#### Performance Charts")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # ROI trend
        from datetime import timedelta
        now = datetime.now()
        x = [now - timedelta(hours=i) for i in range(24, 0, -1)]
        y = [random.uniform(-5, 15) for _ in range(24)]
        
        fig = create_line_chart(
            x=x,
            y=y,
            title="24h ROI Trend",
            x_label="Time",
            y_label="ROI (%)",
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Position count
        x = [now - timedelta(hours=i) for i in range(24, 0, -1)]
        y = [random.randint(0, 5) for _ in range(24)]
        
        fig = create_line_chart(
            x=x,
            y=y,
            title="Position Count History",
            x_label="Time",
            y_label="Positions",
        )
        
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("#### Configuration Editor")
    
    # Sample config
    config_yaml = f"""# Bot {selected_bot_id} Configuration
strategy_type: Strategy_{selected_bot_id}
capital_allocated: 5000.0
max_positions: 5
kelly_fraction: 0.5  # Half Kelly
zone_restriction: [1, 2, 3]

risk:
  max_drawdown: 0.25
  consecutive_loss_limit: 3
  daily_loss_limit: 0.05
"""
    
    edited_config = st.text_area(
        "YAML Configuration",
        value=config_yaml,
        height=300,
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Save Config", type="primary"):
            st.success("Configuration saved successfully!")
            # TODO: Implement save config API call
    
    with col2:
        if st.button("🔄 Reload Default"):
            st.info("Configuration reloaded to defaults.")
            st.rerun()

with tab3:
    st.markdown("#### Bot Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("▶️ START", type="primary", use_container_width=True):
            st.success(f"Bot {selected_bot_id} started.")
            # TODO: Implement start API call
    
    with col2:
        if st.button("⏸️ PAUSE", use_container_width=True):
            st.info(f"Bot {selected_bot_id} paused.")
            # TODO: Implement pause API call
    
    with col3:
        if st.button("⏹️ STOP", use_container_width=True):
            st.warning(f"Bot {selected_bot_id} stopped.")
            # TODO: Implement stop API call
    
    with col4:
        if st.button("🛑 EMERGENCY HALT", use_container_width=True):
            if st.checkbox(f"Confirm emergency halt Bot {selected_bot_id}"):
                st.error(f"Bot {selected_bot_id} emergency halt triggered!")
                # TODO: Implement emergency halt API call

with tab4:
    st.markdown("#### Live Logs")
    
    # Sample logs
    logs = [
        f"{datetime.now().strftime('%H:%M:%S')} - INFO - Bot {selected_bot_id} cycle executed",
        f"{datetime.now().strftime('%H:%M:%S')} - INFO - Market scan completed: 15 opportunities",
        f"{datetime.now().strftime('%H:%M:%S')} - DEBUG - Risk validation passed",
        f"{datetime.now().strftime('%H:%M:%S')} - INFO - Order placed: market_abc123",
        f"{datetime.now().strftime('%H:%M:%S')} - INFO - Position opened: pos_xyz789",
    ]
    
    log_level = st.selectbox("Filter by level", ["ALL", "INFO", "DEBUG", "WARNING", "ERROR"])
    
    st.text_area(
        "Recent Logs (Last 50)",
        value="\n".join(logs),
        height=200,
        disabled=True,
    )
    
    if st.button("🔄 Refresh Logs"):
        st.rerun()

# Auto-refresh indicator
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Auto-refresh: 2s")

# Auto-refresh (2s)
time.sleep(2)
st.rerun()
