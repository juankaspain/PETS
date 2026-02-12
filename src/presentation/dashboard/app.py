"""Main Streamlit dashboard application."""

import streamlit as st

# Page config
st.set_page_config(
    page_title="PETS - Polymarket Elite Trading System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar
st.sidebar.title("🤖 PETS Dashboard")
st.sidebar.markdown("**Polymarket Elite Trading System**")
st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio(
    "Navigation",
    [
        "📊 Overview",
        "🤖 Bot Management",
        "💼 Positions",
        "🏪 Markets",
        "⚠️ Risk",
        "📈 Analytics",
        "⚙️ Settings",
    ],
)

# API endpoint configuration
api_base_url = st.sidebar.text_input(
    "API Endpoint",
    value="http://localhost:8000",
    help="FastAPI backend URL",
)

# Auto-refresh
auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
if auto_refresh:
    refresh_rate = st.sidebar.slider("Refresh rate (seconds)", 10, 120, 30)

st.sidebar.markdown("---")
st.sidebar.markdown("**Bot 8: Volatility Skew**")
st.sidebar.markdown("💰 $106K Evidence")

# Main content
st.title(page)

if page == "📊 Overview":
    st.markdown("""
    ### Portfolio Overview
    
    Real-time monitoring of your Polymarket trading portfolio.
    
    **Key Metrics:**
    - Portfolio value and P&L
    - Active bots and their states
    - Open positions summary
    - Circuit breaker status
    """)
    
    # Placeholder for overview page
    st.info("Overview page - See pages/1_overview.py for full implementation")

elif page == "🤖 Bot Management":
    st.markdown("""
    ### Bot Management
    
    Control and configure your trading bots.
    
    **Features:**
    - Start/stop bots
    - Create new bots
    - Edit bot configuration
    - View bot performance
    """)
    
    st.info("Bot Management page - See pages/2_bot_management.py for full implementation")

elif page == "💼 Positions":
    st.markdown("""
    ### Positions
    
    Monitor and manage your trading positions.
    
    **Features:**
    - Open positions table
    - Closed positions history
    - Close positions manually
    - P&L analysis
    """)
    
    st.info("Positions page - See pages/3_positions.py for full implementation")

elif page == "🏪 Markets":
    st.markdown("""
    ### Markets
    
    Browse active Polymarket markets and opportunities.
    
    **Features:**
    - Active markets list
    - Bot 8 opportunity signals
    - Market filters
    - Market details
    """)
    
    st.info("Markets page - See pages/4_markets.py for full implementation")

elif page == "⚠️ Risk":
    st.markdown("""
    ### Risk Management
    
    Monitor portfolio risk and circuit breakers.
    
    **Features:**
    - Portfolio risk metrics (VaR, drawdown)
    - Circuit breaker status
    - Zone exposure
    - Position risk heatmap
    """)
    
    st.info("Risk page - See pages/5_risk.py for full implementation")

elif page == "📈 Analytics":
    st.markdown("""
    ### Analytics
    
    Analyze trading performance and patterns.
    
    **Features:**
    - Equity curve
    - Daily P&L chart
    - Trade analysis
    - Win rate and profit factor
    """)
    
    st.info("Analytics page - See pages/6_analytics.py for full implementation")

elif page == "⚙️ Settings":
    st.markdown("""
    ### Settings
    
    Configure system settings and preferences.
    
    **Features:**
    - API endpoint configuration
    - Refresh rate
    - Theme settings
    - Database health check
    """)
    
    st.info("Settings page - See pages/7_settings.py for full implementation")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Status:** 🟢 Connected")
st.sidebar.markdown(f"**API:** {api_base_url}")
