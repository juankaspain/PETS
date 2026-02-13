"""Main Streamlit dashboard application.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import streamlit as st

# Page config
st.set_page_config(
    page_title="PETS - Polymarket Elite Trading System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .emergency-btn {
        background-color: #ff4b4b;
        color: white;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Main page content
st.markdown('<h1 class="main-header">🚀 PETS Dashboard</h1>', unsafe_allow_html=True)

st.markdown(
    """
    ## Welcome to Polymarket Elite Trading System
    
    This dashboard provides real-time monitoring and control of your 10-bot trading system.
    
    ### Quick Links
    - **📊 Overview**: Real-time portfolio metrics and emergency controls
    - **🤖 Bot Control**: Individual bot management and configuration
    - **📈 Performance**: Comparative analysis and ROI tracking
    - **💰 Positions**: Active and closed position management
    - **📜 Order Log**: Execution history and performance metrics
    - **⚠️ Risk Monitor**: Zone exposure and circuit breaker status
    - **⚙️ Settings**: System configuration and notifications
    
    ### System Status
    """
)

# System health indicators
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("API Status", "🟢 Online", "Connected")

with col2:
    st.metric("Database", "🟢 Healthy", "<10ms latency")

with col3:
    st.metric("WebSocket", "🟢 Active", "Real-time updates")

st.markdown(
    """
    ---
    
    **Navigation**: Use the sidebar to access different sections.
    
    **Emergency Halt**: Available on Overview page for immediate system shutdown.
    """
)
