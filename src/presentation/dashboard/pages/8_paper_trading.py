"""Paper Trading page."""

import streamlit as st

from src.presentation.dashboard.components.api_client import APIClient

st.set_page_config(page_title="Paper Trading", page_icon="🧪", layout="wide")

st.title("🧪 Paper Trading")

st.markdown("""
Test Bot 8 Volatility Skew strategy with simulated capital before going live.

**Zero Risk Testing:**
- Virtual $10K starting balance
- Real market data, simulated execution
- Track paper P&L and performance
- Validate strategy without risk
""")

st.markdown("---")

# API client
api_base_url = st.session_state.get("api_base_url", "http://localhost:8000")
client = APIClient(api_base_url)

# Fetch paper wallet
try:
    wallet = client.get_paper_wallet()
    metrics = client.get_paper_metrics()
    positions = client.get_paper_positions()
except Exception as e:
    st.error(f"Failed to fetch paper trading data: {e}")
    st.stop()

# Wallet Overview
st.subheader("💰 Paper Wallet")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Value",
        f"${wallet['total_value']:,.2f}",
        delta=f"${wallet['total_return']:,.2f} ({wallet['total_return_pct']:.2f}%)",
    )

with col2:
    st.metric(
        "Cash Balance",
        f"${wallet['balance']:,.2f}",
    )

with col3:
    st.metric(
        "Realized P&L",
        f"${wallet['realized_pnl']:,.2f}",
    )

with col4:
    st.metric(
        "Unrealized P&L",
        f"${wallet['unrealized_pnl']:,.2f}",
    )

st.markdown("---")

# Performance Metrics
st.subheader("📈 Performance Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Trades",
        wallet['total_trades'],
    )

with col2:
    st.metric(
        "Win Rate",
        f"{wallet['win_rate']:.1f}%",
        delta=f"{wallet['winning_trades']}W / {wallet['losing_trades']}L",
    )

with col3:
    st.metric(
        "Profit Factor",
        f"{metrics['profit_factor']:.2f}",
    )

with col4:
    if metrics['avg_win'] > 0:
        st.metric(
            "Avg Win / Loss",
            f"${metrics['avg_win']:.2f} / ${metrics['avg_loss']:.2f}",
        )
    else:
        st.metric("Avg Win / Loss", "N/A")

st.markdown("---")

# Positions
st.subheader("💼 Paper Positions")

tab1, tab2 = st.tabs(["📈 Open Positions", "📊 Closed Positions"])

with tab1:
    open_positions = [pos for pos in positions if pos['is_open']]
    
    if open_positions:
        st.dataframe(
            [
                {
                    "Market": pos["market_id"][:16] + "...",
                    "Side": pos["side"],
                    "Size": f"${pos['size']:,.0f}",
                    "Entry": f"{pos['entry_price']:.4f}",
                    "Current": f"{pos['current_price']:.4f}" if pos['current_price'] else "N/A",
                    "Unrealized P&L": f"${pos['unrealized_pnl']:,.2f}" if pos['unrealized_pnl'] else "N/A",
                    "Zone": f"Z{pos['zone']}",
                }
                for pos in open_positions
            ],
            use_container_width=True,
        )
    else:
        st.info("No open paper positions")

with tab2:
    closed_positions = [pos for pos in positions if not pos['is_open']]
    
    if closed_positions:
        st.dataframe(
            [
                {
                    "Market": pos["market_id"][:16] + "...",
                    "Side": pos["side"],
                    "Size": f"${pos['size']:,.0f}",
                    "Entry": f"{pos['entry_price']:.4f}",
                    "Exit": f"{pos['exit_price']:.4f}" if pos['exit_price'] else "N/A",
                    "Realized P&L": f"${pos['realized_pnl']:,.2f}" if pos['realized_pnl'] else "N/A",
                    "P&L %": f"{(pos['realized_pnl']/pos['size']*100):.2f}%" if pos['realized_pnl'] and pos['size'] else "N/A",
                    "Zone": f"Z{pos['zone']}",
                }
                for pos in closed_positions
            ],
            use_container_width=True,
        )
    else:
        st.info("No closed paper positions yet")

st.markdown("---")

# Actions
st.subheader("⚙️ Actions")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Reset Paper Wallet**")
    st.markdown("Clear all positions and reset balance to $10K")
    
    if st.button("🔄 Reset Wallet", type="primary"):
        try:
            result = client.reset_paper_wallet()
            st.success(f"✅ {result['message']}")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to reset wallet: {e}")

with col2:
    st.markdown("**Paper Trading Status**")
    if wallet['total_trades'] > 0:
        st.success("🟢 Active - Testing Bot 8 strategy")
    else:
        st.info("🟡 Ready - Start paper trading to test Bot 8")

st.markdown("---")

# Info
st.info("""
**How Paper Trading Works:**

1. **Virtual Capital**: Start with $10K simulated balance
2. **Real Market Data**: Monitor live Polymarket prices
3. **Simulated Execution**: Orders filled based on market prices
4. **Zero Risk**: No real money, no blockchain transactions
5. **Track Performance**: Monitor win rate, profit factor, P&L
6. **Validate Strategy**: Prove Bot 8 works before going live

**Bot 8 Strategy:**
- Entry: Buy YES <0.20 OR expensive NO >0.80 when spread >15%
- Hold: 24-48h for mean reversion
- Exit: 0.25-0.35 delta improvement OR 10% stop-loss
- Position Sizing: Half Kelly with 65% win probability
- Risk Management: Circuit breakers active

**Target Performance:**
- Win Rate: ≥60% (evidence: 65%)
- Profit Factor: ≥1.5
- Max Drawdown: ≤15%
- Sharpe Ratio: ≥1.0
""")
