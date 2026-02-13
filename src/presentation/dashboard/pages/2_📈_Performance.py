"""Performance page.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import asyncio

import pandas as pd
import streamlit as st

from src.presentation.dashboard.api_client import APIClient
from src.presentation.dashboard.utils import format_currency, format_percentage

st.set_page_config(page_title="Performance", page_icon="📈", layout="wide")

st.title("📈 Performance Analysis")

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


bots = asyncio.run(load_bots())

if not bots:
    st.info("No bots to analyze.")
else:
    # Comparative table
    st.subheader("Bot Comparison")
    
    df_data = []
    for bot in bots:
        df_data.append({
            "Bot ID": bot.get("bot_id"),
            "Strategy": bot.get("strategy_type"),
            "State": bot.get("state"),
            "Capital": bot.get("capital_allocated", 0),
            "P&L": bot.get("total_pnl", 0),
            "ROI": bot.get("roi", 0),
        })
    
    df = pd.DataFrame(df_data)
    
    st.dataframe(
        df.style.format({
            "Capital": "${:,.2f}",
            "P&L": "${:,.2f}",
            "ROI": "{:.2%}",
        }),
        use_container_width=True,
    )
    
    st.divider()
    
    # Portfolio metrics
    st.subheader("Portfolio Overview")
    
    async def load_portfolio():
        """Load portfolio metrics."""
        try:
            return await api_client.get_portfolio_metrics()
        except Exception as e:
            st.error(f"Error loading portfolio: {e}")
            return {}
    
    portfolio = asyncio.run(load_portfolio())
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Capital",
            format_currency(portfolio.get("total_capital", 0)),
        )
    
    with col2:
        st.metric(
            "Total P&L",
            format_currency(portfolio.get("total_pnl", 0)),
            delta=format_percentage(portfolio.get("portfolio_roi", 0)),
        )
    
    with col3:
        st.metric(
            "Win Rate",
            format_percentage(portfolio.get("win_rate", 0)),
        )
    
    with col4:
        st.metric(
            "Sharpe Ratio",
            f"{portfolio.get('sharpe_ratio', 0):.2f}",
        )
