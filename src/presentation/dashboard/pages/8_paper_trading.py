"""Paper Trading page."""

import streamlit as st
from datetime import datetime, timedelta

from src.presentation.dashboard.components.api_client import APIClient

st.set_page_config(page_title="Paper Trading", page_icon="🧪", layout="wide")

st.title("🧪 Paper Trading")

st.markdown("""
Test Bot 8 strategy without real money. Validate performance before production.
""")

# API client
api_base_url = st.session_state.get("api_base_url", "http://localhost:8000")
client = APIClient(api_base_url)

st.markdown("---")

# Paper Trading Session
st.subheader("🔋 Paper Trading Session")

col1, col2 = st.columns([2, 1])

with col1:
    if "paper_session_id" not in st.session_state:
        # Not started - show start form
        with st.form("start_paper_trading"):
            initial_balance = st.number_input(
                "Initial Balance ($)",
                min_value=1000,
                max_value=100000,
                value=10000,
                step=1000,
            )
            
            st.markdown("**Bot 8 Configuration:**")
            spread_threshold = st.slider("Spread Threshold", 0.10, 0.30, 0.15, 0.01)
            entry_low = st.slider("Entry Threshold (Low)", 0.05, 0.30, 0.20, 0.01)
            
            if st.form_submit_button("▶️ Start Paper Trading"):
                try:
                    # Start paper trading
                    response = client._request(
                        "POST",
                        "/api/paper-trading/start",
                        json={
                            "initial_balance": initial_balance,
                            "strategy_config": {
                                "spread_threshold": spread_threshold,
                                "entry_threshold_low": entry_low,
                                "entry_threshold_high": 1.0 - entry_low,
                                "hold_hours_min": 24,
                                "hold_hours_max": 48,
                                "target_delta": 0.30,
                                "stop_loss_pct": 0.10,
                            },
                        },
                    )
                    
                    st.session_state["paper_session_id"] = response["session_id"]
                    st.success("Paper trading session started!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to start paper trading: {e}")
    else:
        # Started - show status
        try:
            status = client._request(
                "GET",
                "/api/paper-trading/status",
                params={"session_id": st.session_state["paper_session_id"]},
            )
            
            st.success("✅ Paper Trading Active")
            
            # Metrics
            col_a, col_b, col_c, col_d = st.columns(4)
            
            with col_a:
                st.metric(
                    "Balance",
                    f"${status['current_balance']:,.2f}",
                    delta=f"${status['total_pnl']:,.2f}",
                )
            
            with col_b:
                st.metric(
                    "Return",
                    f"{status['return_pct']:.2f}%",
                )
            
            with col_c:
                st.metric(
                    "Trades",
                    status['total_trades'],
                    delta=f"{status['winning_trades']}W / {status['losing_trades']}L",
                )
            
            with col_d:
                st.metric(
                    "Win Rate",
                    f"{status['win_rate']*100:.1f}%",
                )
            
            # Stop button
            if st.button("⏸️ Stop Paper Trading"):
                del st.session_state["paper_session_id"]
                st.rerun()
        
        except Exception as e:
            st.error(f"Failed to fetch status: {e}")
            if st.button("Clear Session"):
                del st.session_state["paper_session_id"]
                st.rerun()

with col2:
    st.info("""
    **Paper Trading**
    
    - No real money
    - Virtual $10K balance
    - Real market data
    - Bot 8 strategy active
    - Track performance
    """)

st.markdown("---")

# Paper Trades
if "paper_session_id" in st.session_state:
    st.subheader("📊 Paper Trades")
    
    try:
        trades = client._request(
            "GET",
            "/api/paper-trading/trades",
            params={
                "session_id": st.session_state["paper_session_id"],
                "limit": 100,
            },
        )
        
        if trades:
            st.dataframe(
                [
                    {
                        "Market": trade["market_id"][:12] + "...",
                        "Side": trade["side"],
                        "Size": f"${trade['size']:,.0f}",
                        "Entry": f"{trade['entry_price']:.4f}",
                        "Exit": f"{trade['exit_price']:.4f}" if trade['exit_price'] else "N/A",
                        "P&L": f"${trade['realized_pnl']:,.2f}" if trade['realized_pnl'] else "N/A",
                        "Status": "🟢 Win" if trade['realized_pnl'] and trade['realized_pnl'] > 0 else "🔴 Loss" if trade['realized_pnl'] else "Open",
                    }
                    for trade in trades
                ],
                use_container_width=True,
            )
        else:
            st.info("No paper trades yet. Waiting for Bot 8 signals...")
    
    except Exception as e:
        st.error(f"Failed to fetch trades: {e}")

st.markdown("---")

# Backtest
st.subheader("🔬 Backtest")

st.markdown("""
Run historical backtest to validate Bot 8 strategy performance.
""")

col1, col2 = st.columns([2, 1])

with col1:
    with st.form("run_backtest"):
        st.markdown("**Backtest Parameters:**")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now() - timedelta(days=90),
            )
        
        with col_b:
            end_date = st.date_input(
                "End Date",
                value=datetime.now(),
            )
        
        initial_balance = st.number_input(
            "Initial Balance",
            min_value=1000,
            max_value=100000,
            value=10000,
            step=1000,
        )
        
        if st.form_submit_button("🚀 Run Backtest"):
            with st.spinner("Running backtest..."):
                try:
                    # Start backtest
                    response = client._request(
                        "POST",
                        "/api/paper-trading/backtest",
                        json={
                            "start_date": start_date.isoformat(),
                            "end_date": end_date.isoformat(),
                            "initial_balance": initial_balance,
                            "strategy_config": {},
                        },
                    )
                    
                    backtest_id = response["backtest_id"]
                    
                    # Get results
                    result = client._request(
                        "GET",
                        f"/api/paper-trading/backtest/{backtest_id}",
                    )
                    
                    st.session_state["backtest_result"] = result
                    st.success("Backtest completed!")
                    st.rerun()
                
                except Exception as e:
                    st.error(f"Backtest failed: {e}")

with col2:
    st.info("""
    **Backtest**
    
    - Historical data
    - Bot 8 strategy
    - Performance metrics
    - Validate parameters
    """)

# Backtest Results
if "backtest_result" in st.session_state:
    st.markdown("---")
    st.subheader("📈 Backtest Results")
    
    result = st.session_state["backtest_result"]
    
    # Key Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Return",
            f"{result['return_pct']:.2f}%",
            delta=f"${result['total_pnl']:,.2f}",
        )
    
    with col2:
        st.metric(
            "Win Rate",
            f"{result['win_rate']*100:.1f}%",
            delta=f"{result['winning_trades']}W / {result['losing_trades']}L",
        )
    
    with col3:
        st.metric(
            "Profit Factor",
            f"{result['profit_factor']:.2f}",
        )
    
    with col4:
        st.metric(
            "Sharpe Ratio",
            f"{result['sharpe_ratio']:.2f}" if result['sharpe_ratio'] else "N/A",
        )
    
    with col5:
        st.metric(
            "Max Drawdown",
            f"{result['max_drawdown_pct']:.2f}%",
        )
    
    st.markdown("---")
    
    # Validation Checklist
    st.subheader("✅ Validation Checklist")
    
    criteria = [
        {
            "name": "100+ Trades",
            "target": 100,
            "actual": result['total_trades'],
            "passed": result['total_trades'] >= 100,
        },
        {
            "name": "Win Rate ≥60%",
            "target": 0.60,
            "actual": result['win_rate'],
            "passed": result['win_rate'] >= 0.60,
        },
        {
            "name": "Profit Factor ≥1.5",
            "target": 1.5,
            "actual": result['profit_factor'],
            "passed": result['profit_factor'] >= 1.5,
        },
        {
            "name": "Max Drawdown ≤15%",
            "target": 15,
            "actual": result['max_drawdown_pct'],
            "passed": result['max_drawdown_pct'] <= 15,
        },
    ]
    
    if result['sharpe_ratio']:
        criteria.append({
            "name": "Sharpe Ratio ≥1.0",
            "target": 1.0,
            "actual": result['sharpe_ratio'],
            "passed": result['sharpe_ratio'] >= 1.0,
        })
    
    for criterion in criteria:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(criterion["name"])
        
        with col2:
            st.write(f"Target: {criterion['target']}")
        
        with col3:
            status = "✅ PASS" if criterion["passed"] else "❌ FAIL"
            st.write(f"{status} ({criterion['actual']:.2f})")
    
    # Overall validation
    all_passed = all(c["passed"] for c in criteria)
    
    if all_passed:
        st.success("🎉 **ALL CRITERIA PASSED** - Ready for production!")
    else:
        st.warning("⚠️ Some criteria not met. Review strategy parameters.")
    
    # Clear button
    if st.button("Clear Backtest Results"):
        del st.session_state["backtest_result"]
        st.rerun()
