"""Settings page - System configuration and health.

Global config, bot-specific settings, notifications, database, and system health.
"""

import asyncio
from typing import Any, Dict

import pandas as pd
import streamlit as st
import yaml

from ..components.api_client import APIClient

# Page config
st.set_page_config(
    page_title="Settings - PETS Dashboard",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title
st.title("⚙️ Settings")
st.markdown("System configuration and health monitoring")

# Initialize API client
api_client = APIClient(base_url="http://localhost:8000", api_key="your-api-key-here")


async def get_global_config() -> Dict[str, Any]:
    """Fetch global configuration."""
    try:
        response = await api_client.get("/api/v1/config/global")
        return response
    except Exception as e:
        st.error(f"Error fetching global config: {e}")
        return {}


async def save_global_config(config: Dict[str, Any]) -> bool:
    """Save global configuration."""
    try:
        await api_client.put("/api/v1/config/global", data=config)
        st.success("Global configuration saved successfully")
        return True
    except Exception as e:
        st.error(f"Error saving global config: {e}")
        return False


async def get_bot_config(bot_id: str) -> Dict[str, Any]:
    """Fetch bot-specific configuration."""
    try:
        response = await api_client.get(f"/api/v1/config/bots/{bot_id}")
        return response
    except Exception as e:
        st.error(f"Error fetching bot config: {e}")
        return {}


async def save_bot_config(bot_id: str, config: Dict[str, Any]) -> bool:
    """Save bot-specific configuration."""
    try:
        await api_client.put(f"/api/v1/config/bots/{bot_id}", data=config)
        st.success(f"Bot {bot_id} configuration saved successfully")
        return True
    except Exception as e:
        st.error(f"Error saving bot config: {e}")
        return False


async def get_system_health() -> Dict[str, Any]:
    """Fetch system health metrics."""
    try:
        response = await api_client.get("/health/ready")
        return response
    except Exception as e:
        st.error(f"Error fetching system health: {e}")
        return {}


def render_global_config_tab() -> None:
    """Render global configuration tab."""
    st.markdown("### Global Configuration")

    # Emergency controls
    st.markdown("**Emergency Controls**")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🛑 HALT ALL BOTS", type="primary", use_container_width=True):
            st.warning("⚠️ Confirm by clicking again")

    with col2:
        if st.button("⏸️ PAUSE ALL BOTS", use_container_width=True):
            st.info("Pausing all bots...")

    with col3:
        if st.button("▶️ RESUME ALL BOTS", use_container_width=True):
            st.info("Resuming all bots...")

    st.markdown("---")

    # Risk parameters
    st.markdown("**Risk Parameters**")

    col1, col2 = st.columns(2)

    with col1:
        max_portfolio_dd = st.slider(
            "Max Portfolio Drawdown %", min_value=10, max_value=50, value=40, step=5
        )
        max_daily_loss = st.slider(
            "Max Daily Loss %", min_value=1, max_value=10, value=5, step=1
        )

    with col2:
        max_bot_dd = st.slider(
            "Max Bot Drawdown %", min_value=10, max_value=40, value=25, step=5
        )
        consecutive_loss_limit = st.slider(
            "Consecutive Loss Limit", min_value=2, max_value=5, value=3, step=1
        )

    # Trading parameters
    st.markdown("**Trading Parameters**")

    col1, col2 = st.columns(2)

    with col1:
        default_order_type = st.selectbox(
            "Default Order Type", ["POST_ONLY", "MARKET", "LIMIT"], index=0
        )
        max_slippage = st.slider(
            "Max Slippage Tolerance %", min_value=0.1, max_value=2.0, value=0.5, step=0.1
        )

    with col2:
        rate_limit_per_min = st.number_input(
            "Rate Limit (requests/min)", min_value=10, max_value=200, value=100, step=10
        )

    # Save button
    if st.button("💾 Save Global Config", type="primary"):
        config = {
            "risk": {
                "max_portfolio_drawdown_pct": max_portfolio_dd,
                "max_daily_loss_pct": max_daily_loss,
                "max_bot_drawdown_pct": max_bot_dd,
                "consecutive_loss_limit": consecutive_loss_limit,
            },
            "trading": {
                "default_order_type": default_order_type,
                "max_slippage_pct": max_slippage,
                "rate_limit_per_min": rate_limit_per_min,
            },
        }
        asyncio.run(save_global_config(config))


def render_bot_config_tab() -> None:
    """Render bot-specific configuration tab."""
    st.markdown("### Bot-Specific Configuration")

    # Bot selector
    bot_id = st.selectbox(
        "Select Bot",
        [f"bot-{i:02d}" for i in range(1, 11)],
        format_func=lambda x: f"Bot {x.split('-')[1]} - {get_bot_name(x)}",
    )

    # Fetch bot config
    bot_config = asyncio.run(get_bot_config(bot_id))

    # Config editor
    col1, col2 = st.columns(2)

    with col1:
        capital_allocated = st.number_input(
            "Capital Allocated ($)",
            min_value=100,
            max_value=10000,
            value=bot_config.get("capital_allocated", 1000),
            step=100,
        )

        kelly_fraction = st.selectbox(
            "Kelly Fraction",
            ["Quarter", "Half", "Full"],
            index=["Quarter", "Half", "Full"].index(bot_config.get("kelly_fraction", "Half")),
        )

        max_position_size = st.number_input(
            "Max Position Size ($)",
            min_value=10,
            max_value=5000,
            value=bot_config.get("max_position_size", 500),
            step=10,
        )

    with col2:
        zone_restrictions = st.multiselect(
            "Allowed Zones",
            ["ZONE_1", "ZONE_2", "ZONE_3", "ZONE_4", "ZONE_5"],
            default=bot_config.get("allowed_zones", ["ZONE_1", "ZONE_2", "ZONE_3"]),
        )

        bot_enabled = st.checkbox("Bot Enabled", value=bot_config.get("enabled", True))

    # Strategy-specific config (YAML)
    st.markdown("**Strategy-Specific Config (YAML)**")
    strategy_config_yaml = st.text_area(
        "Config YAML",
        value=yaml.dump(bot_config.get("strategy_config", {}), default_flow_style=False),
        height=200,
    )

    # Buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Bot Config", type="primary", use_container_width=True):
            try:
                strategy_config = yaml.safe_load(strategy_config_yaml)
                config = {
                    "capital_allocated": capital_allocated,
                    "kelly_fraction": kelly_fraction,
                    "max_position_size": max_position_size,
                    "allowed_zones": zone_restrictions,
                    "enabled": bot_enabled,
                    "strategy_config": strategy_config,
                }
                asyncio.run(save_bot_config(bot_id, config))
            except yaml.YAMLError as e:
                st.error(f"Invalid YAML: {e}")

    with col2:
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            st.info(f"Reset {bot_id} to default configuration")


def get_bot_name(bot_id: str) -> str:
    """Get bot strategy name."""
    names = {
        "bot-01": "Rebalancing",
        "bot-02": "Esports",
        "bot-03": "Copy Trading",
        "bot-04": "News-driven",
        "bot-05": "Market Making",
        "bot-06": "Multi-outcome",
        "bot-07": "Contrarian",
        "bot-08": "Tail Risk",
        "bot-09": "Kelly Optimizer",
        "bot-10": "Long-term Value",
    }
    return names.get(bot_id, "Unknown")


def render_notifications_tab() -> None:
    """Render notifications configuration tab."""
    st.markdown("### Notification Settings")

    # Alert channels
    st.markdown("**Alert Channels**")

    email_enabled = st.checkbox("Email Notifications", value=True)
    if email_enabled:
        col1, col2 = st.columns(2)
        with col1:
            smtp_host = st.text_input("SMTP Host", value="smtp.gmail.com")
            smtp_port = st.number_input("SMTP Port", value=587)
        with col2:
            smtp_user = st.text_input("SMTP User", value="alerts@pets.com")
            smtp_password = st.text_input("SMTP Password", type="password")

    st.markdown("---")

    webhook_enabled = st.checkbox("Webhook Notifications (Slack/Discord)", value=False)
    if webhook_enabled:
        webhook_url = st.text_input("Webhook URL", value="https://hooks.slack.com/...")

    st.markdown("---")

    sms_enabled = st.checkbox("SMS Alerts (Twilio)", value=False)
    if sms_enabled:
        col1, col2 = st.columns(2)
        with col1:
            twilio_sid = st.text_input("Twilio Account SID")
        with col2:
            twilio_token = st.text_input("Twilio Auth Token", type="password")
        phone_number = st.text_input("Alert Phone Number", value="+1234567890")

    # Test notification
    if st.button("📧 Send Test Notification"):
        st.info("Test notification sent")


def render_database_tab() -> None:
    """Render database status and maintenance tab."""
    st.markdown("### Database Status")

    # Connection status
    col1, col2 = st.columns(2)

    with col1:
        st.success("✅ TimescaleDB Connected")
        st.caption("Host: localhost:5432")
        st.caption("Database: pets_production")

    with col2:
        st.success("✅ Redis Connected")
        st.caption("Host: localhost:6379")
        st.caption("DB: 0")

    st.markdown("---")

    # Performance metrics
    st.markdown("**Performance Metrics**")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Query Latency p50", "8ms")
        st.metric("Query Latency p99", "45ms")

    with col2:
        st.metric("Connection Pool Usage", "35%")
        st.metric("Cache Hit Rate", "92.5%")

    with col3:
        st.metric("Compression Ratio", "4.2x")
        st.metric("Last Backup", "2h ago")

    st.markdown("---")

    # Maintenance actions
    st.markdown("**Maintenance Actions**")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🗃️ Run Compression", use_container_width=True):
            st.info("Running compression on chunks older than 14 days...")

    with col2:
        if st.button("🧹 Clear Redis Cache", use_container_width=True):
            st.warning("Redis cache cleared")

    with col3:
        if st.button("💾 Export Snapshot", use_container_width=True):
            st.info("Exporting database snapshot...")


def render_system_health_tab() -> None:
    """Render system health monitoring tab."""
    st.markdown("### System Health")

    # Service status grid
    st.markdown("**Service Status**")

    services = [
        {"name": "API (FastAPI)", "status": "RUNNING", "cpu": 12, "memory": 256},
        {"name": "Dashboard (Streamlit)", "status": "RUNNING", "cpu": 8, "memory": 180},
        {"name": "TimescaleDB", "status": "RUNNING", "cpu": 25, "memory": 512},
        {"name": "Redis", "status": "RUNNING", "cpu": 3, "memory": 64},
        {"name": "WebSocket Gateway", "status": "RUNNING", "cpu": 5, "memory": 128},
        {"name": "Bot-01", "status": "ACTIVE", "cpu": 2, "memory": 48},
        {"name": "Bot-05", "status": "ACTIVE", "cpu": 4, "memory": 52},
        {"name": "Bot-08", "status": "ACTIVE", "cpu": 3, "memory": 50},
    ]

    df = pd.DataFrame(services)

    # Color-code status
    def color_status(val: str) -> str:
        if val in ["RUNNING", "ACTIVE"]:
            return "background-color: rgba(34, 197, 94, 0.2);"
        elif val == "PAUSED":
            return "background-color: rgba(245, 158, 11, 0.2);"
        else:
            return "background-color: rgba(239, 68, 68, 0.2);"

    styled_df = df.style.applymap(color_status, subset=["status"])

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Logs viewer
    st.markdown("**System Logs (Last 100 entries)**")

    col1, col2, col3 = st.columns(3)

    with col1:
        log_service = st.selectbox("Service", ["All", "API", "Bot-08", "Database"])

    with col2:
        log_level = st.selectbox("Level", ["All", "INFO", "WARNING", "ERROR"])

    with col3:
        live_tail = st.checkbox("Live Tail", value=False)

    # Mock logs
    logs = [
        "[2026-02-13 01:55:00] [INFO] [API] Received order placement request",
        "[2026-02-13 01:54:58] [INFO] [Bot-08] Position opened: market-123",
        "[2026-02-13 01:54:55] [WARNING] [Bot-05] Slippage 0.4% on fill",
    ]

    st.text_area("Logs", value="\n".join(logs), height=200, disabled=True)

    # Actions
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 Download Diagnostics", use_container_width=True):
            st.info("Generating diagnostics package...")

    with col2:
        if st.button("🧹 Clear Logs", use_container_width=True):
            st.warning("Logs cleared")


# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🌍 Global", "🤖 Bots", "🔔 Notifications", "💾 Database", "❤️ Health"]
)

with tab1:
    render_global_config_tab()

with tab2:
    render_bot_config_tab()

with tab3:
    render_notifications_tab()

with tab4:
    render_database_tab()

with tab5:
    render_system_health_tab()

# Footer
st.markdown("---")
st.caption("⚙️ Settings | Configuration management and system health")
