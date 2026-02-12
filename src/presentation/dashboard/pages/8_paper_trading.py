"""Paper Trading page."""

import streamlit as st
from datetime import datetime, timedelta

from src.presentation.dashboard.components.api_client import APIClient

st.set_page_config(page_title="Paper Trading", page_icon="🧪", layout="wide")

st.title("🧪 Paper Trading")

st.markdown("""
Test Bot 8 strategy with virtual money before risking real capital.

**Features:**
- Virtual $10K balance
- Real-time market simulation
- Full Bot 8 strategy execution
- Performance tracking
- No blockchain transactions
""")

st.markdown("---")

# API client
api_base_url = st.session_state.get("api_base_url", "http://localhost:8000")
client = APIClient(api_base_url)

# Session management
if "paper_trading_session_id" not in st.session_state:
    st.session_state["paper_trading_session_id"] = None

session_id = st.session_state["paper_trading_session_id"]

# Control panel
st.subheader("🎮 Control Panel")

col1, col2, col3 = st.columns(3)

with col1:
    if not session_id:
        initial_balance = st.number_input(
            "Initial Balance",
            min_value=1000,
            max_value=100000,
            value=10000,
            step=1000,
        )
        
        if st.button("▶️ Start Paper Trading", type="primary", use_container_width=True):
            try:
                response = client.session.post(
                    f"{api_base_url}/api/paper-trading/start",
                    json={
                        "initial_balance": initial_balance,
                        "bot_config": None,  # Use defaults
                    },
                )
                response.raise_for_status()
                data = response.json()
                st.session_state["paper_trading_session_id"] = data["session_id"]
                st.success(f"Paper trading started! Session: {data['session_id'][:16]}...")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to start: {e}")
    else:
        if st.button("⏹️ Stop Paper Trading", type="secondary", use_container_width=True):
            try:
                response = client.session.post(
                    f"{api_base_url}/api/paper-trading/stop/{session_id}"
                )
                response.raise_for_status()
                st.session_state["paper_trading_session_id"] = None
                st.success("Paper trading stopped!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to stop: {e}")

with col2:
    if session_id:
        st.metric("Session ID", session_id[:16] + "...")

with col3:
    if session_id:
        try:
            response = client.session.get(
                f"{api_base_url}/api/paper-trading/status/{session_id}"
            )
            response.raise_for_status()
            status = response.json()
            
            status_emoji = "🟢" if status["is_running"] else "🔴"
            st.metric("Status", f"{status_emoji} {'Running' if status['is_running'] else 'Stopped'}")
        except Exception as e:
            st.error(f"Failed to fetch status: {e}")

st.markdown("---")

# Wallet state
if session_id:
    st.subheader("💰 Wallet State")
    
    try:
        # Fetch status
        status_response = client.session.get(
            f"{api_base_url}/api/paper-trading/status/{session_id}"
        )
        status_response.raise_for_status()
        status = status_response.json()
        
        # Fetch wallet
        wallet_response = client.session.get(
            f"{api_base_url}/api/paper-trading/wallet/{session_id}"
        )
        wallet_response.raise_for_status()
        wallet = wallet_response.json()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Value",
                f"${float(status['total_value']):,.2f}",
                delta=f"${float(status['total_pnl']):,.2f}",
            )
        
        with col2:
            return_pct = (
                (float(status['total_value']) - float(status['initial_balance']))
                / float(status['initial_balance'])
                * 100
            )
            st.metric(
                "Return",
                f"{return_pct:.2f}%",
            )
        
        with col3:
            st.metric(
                "Win Rate",
                f"{float(status['win_rate'])*100:.1f}%",
                delta=f"{status['closed_positions']} trades",
            )
        
        with col4:
            st.metric(
                "Open Positions",
                status["open_positions"],
            )
        
        st.markdown("---")
        
        # Positions
        tab1, tab2 = st.tabs(["Open Positions", "Closed Positions"])
        
        with tab1:
            if wallet["open_positions"]:
                st.dataframe(
                    [
                        {
                            "Market": pos["market_id"][:16] + "...",
                            "Side": pos["side"],
                            "Size": f"${pos['size']:,.0f}",
                            "Entry": f"{pos['entry_price']:.4f}",
                            "Opened": pos["opened_at"][:19],
                        }
                        for pos in wallet["open_positions"]
                    ],
                    use_container_width=True,
                )
            else:
                st.info("No open positions")
        
        with tab2:
            if wallet["closed_positions"]:
                st.dataframe(
                    [
                        {
                            "Market": pos["market_id"][:16] + "...",
                            "Side": pos["side"],
                            "Entry": f"{pos['entry_price']:.4f}",
                            "Exit": f"{pos['exit_price']:.4f}" if pos.get('exit_price') else "N/A",
                            "P&L": f"${pos['realized_pnl']:,.2f}" if pos.get('realized_pnl') else "N/A",
                            "P&L %": f"{(pos['realized_pnl']/pos['size']*100):.2f}%" if pos.get('realized_pnl') else "N/A",
                        }
                        for pos in wallet["closed_positions"]
                    ],
                    use_container_width=True,
                )
            else:
                st.info("No closed positions yet")
    
    except Exception as e:
        st.error(f"Failed to fetch wallet state: {e}")

else:
    st.info("Start a paper trading session to see wallet state")

st.markdown("---")

# Backtesting
st.subheader("🕙 Backtesting")

st.markdown("""
Test Bot 8 strategy on historical data to validate performance.

**Target Metrics (from $106K evidence):**
- Win Rate: 60-70%
- Profit Factor: >1.5
- Max Drawdown: <15%
""")

with st.expander("📈 Run Backtest", expanded=False):
    with st.form("backtest_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            market_id = st.text_input(
                "Market ID",
                value="test_market_1",
                help="Market to backtest on",
            )
            
            start_date = st.date_input(
                "Start Date",
                value=datetime.now() - timedelta(days=90),
            )
        
        with col2:
            initial_balance_bt = st.number_input(
                "Initial Balance",
                min_value=1000,
                max_value=100000,
                value=10000,
                step=1000,
            )
            
            end_date = st.date_input(
                "End Date",
                value=datetime.now(),
            )
        
        submitted = st.form_submit_button("Run Backtest")
        
        if submitted:
            try:
                with st.spinner("Running backtest..."):
                    response = client.session.post(
                        f"{api_base_url}/api/paper-trading/backtest",
                        json={
                            "market_id": market_id,
                            "start_date": start_date.isoformat(),
                            "end_date": end_date.isoformat(),
                            "initial_balance": initial_balance_bt,
                            "bot_config": None,
                        },
                    )
                    response.raise_for_status()
                    result = response.json()
                
                st.success("✅ Backtest completed!")
                
                # Results
                st.subheader("Results")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Final Balance",
                        f"${float(result['final_balance']):,.2f}",
                    )
                    st.metric(
                        "Total Return",
                        f"{float(result['total_return_pct']):.2f}%",
                    )
                
                with col2:
                    st.metric(
                        "Total Trades",
                        result["total_trades"],
                    )
                    st.metric(
                        "Win Rate",
                        f"{float(result['win_rate'])*100:.1f}%",
                    )
                
                with col3:
                    st.metric(
                        "Profit Factor",
                        f"{float(result['profit_factor']):.2f}",
                    )
                    st.metric(
                        "Max Drawdown",
                        f"{float(result['max_drawdown']):.2f}%",
                    )
                
                with col4:
                    st.metric(
                        "Avg Win",
                        f"${float(result['avg_win']):,.2f}",
                    )
                    st.metric(
                        "Avg Loss",
                        f"${float(result['avg_loss']):,.2f}",
                    )
                
                # Validation
                st.subheader("✅ Validation")
                
                win_rate_target = 0.60 <= float(result['win_rate']) <= 0.70
                profit_factor_target = float(result['profit_factor']) >= 1.5
                drawdown_target = float(result['max_drawdown']) <= 15.0
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if win_rate_target:
                        st.success("✅ Win Rate: PASS (60-70%)")
                    else:
                        st.error(f"❌ Win Rate: FAIL ({float(result['win_rate'])*100:.1f}% not in 60-70%)")
                
                with col2:
                    if profit_factor_target:
                        st.success("✅ Profit Factor: PASS (>1.5)")
                    else:
                        st.error(f"❌ Profit Factor: FAIL ({float(result['profit_factor']):.2f} < 1.5)")
                
                with col3:
                    if drawdown_target:
                        st.success("✅ Max Drawdown: PASS (<15%)")
                    else:
                        st.error(f"❌ Max Drawdown: FAIL ({float(result['max_drawdown']):.2f}% > 15%)")
                
            except Exception as e:
                st.error(f"Backtest failed: {e}")
