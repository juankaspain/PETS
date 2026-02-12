"""Markets page."""

import streamlit as st

from src.presentation.dashboard.components.api_client import APIClient

st.set_page_config(page_title="Markets", page_icon="🏪", layout="wide")

st.title("🏪 Markets")

# API client
api_base_url = st.session_state.get("api_base_url", "http://localhost:8000")
client = APIClient(api_base_url)

# Filters
st.subheader("🔍 Filters")

col1, col2, col3 = st.columns(3)

with col1:
    active_only = st.checkbox("Active markets only", value=True)

with col2:
    min_liquidity = st.number_input(
        "Min Liquidity ($)",
        min_value=0,
        max_value=1000000,
        value=10000,
        step=1000,
    )

with col3:
    limit = st.slider("Max results", 10, 200, 50)

st.markdown("---")

# Fetch markets
try:
    markets = client.list_markets(
        active=active_only,
        min_liquidity=min_liquidity,
        limit=limit,
    )
except Exception as e:
    st.error(f"Failed to fetch markets: {e}")
    markets = []

# Markets table
st.subheader(f"📊 Markets ({len(markets)} found)")

if markets:
    for market in markets:
        # Calculate spread
        spread = None
        if market.get("yes_price") and market.get("no_price"):
            spread = abs(float(market["yes_price"]) - 0.5) * 2
        
        # Bot 8 opportunity?
        is_opportunity = False
        if market.get("yes_price"):
            yes_price = float(market["yes_price"])
            if yes_price < 0.20 or yes_price > 0.80:
                is_opportunity = spread and spread > 0.15
        
        opportunity_emoji = "🎯" if is_opportunity else ""
        
        with st.expander(
            f"{opportunity_emoji} {market['question'][:80]}..."
        ):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Liquidity", f"${market['liquidity']:,.0f}")
                st.metric(
                    "Volume 24h",
                    f"${market['volume_24h']:,.0f}" if market.get('volume_24h') else "N/A"
                )
            
            with col2:
                st.metric(
                    "YES Price",
                    f"{float(market['yes_price']):.4f}" if market.get('yes_price') else "N/A"
                )
                st.metric(
                    "NO Price",
                    f"{float(market['no_price']):.4f}" if market.get('no_price') else "N/A"
                )
            
            with col3:
                if spread is not None:
                    st.metric("Spread", f"{spread*100:.1f}%")
                
                if is_opportunity:
                    st.success("🎯 Bot 8 Opportunity!")
                    st.caption("Spread >15% + extreme price")
            
            with col4:
                st.caption(f"Market ID: {market['market_id'][:16]}...")
                st.caption(f"Created: {market['created_at'][:10]}")
                
                if market.get('resolves_at'):
                    st.caption(f"Resolves: {market['resolves_at'][:10]}")
else:
    st.info("No markets found matching filters")
