"""Positions page."""

import streamlit as st

from src.presentation.dashboard.components.api_client import APIClient

st.set_page_config(page_title="Positions", page_icon="💼", layout="wide")

st.title("💼 Positions")

# API client
api_base_url = st.session_state.get("api_base_url", "http://localhost:8000")
client = APIClient(api_base_url)

# Tabs
tab1, tab2 = st.tabs(["📈 Open Positions", "📊 Closed Positions"])

with tab1:
    st.subheader("Open Positions")
    
    try:
        positions = client.list_positions(status="open")
    except Exception as e:
        st.error(f"Failed to fetch positions: {e}")
        positions = []
    
    if positions:
        for pos in positions:
            with st.expander(
                f"{pos['market_id'][:16]}... - {pos['side']} ${pos['size']:,.0f} @ {pos['entry_price']:.4f}"
            ):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Entry Price", f"{pos['entry_price']:.4f}")
                    st.metric("Size", f"${pos['size']:,.0f}")
                    st.metric("Zone", f"Z{pos['zone']}")
                
                with col2:
                    st.metric(
                        "Current Price",
                        f"{pos['current_price']:.4f}" if pos['current_price'] else "N/A"
                    )
                    st.metric(
                        "Unrealized P&L",
                        f"${pos['unrealized_pnl']:,.2f}" if pos['unrealized_pnl'] else "N/A",
                        delta=f"{(pos['unrealized_pnl']/pos['size']*100):.2f}%" if pos['unrealized_pnl'] and pos['size'] else None,
                    )
                
                with col3:
                    # Close position form
                    with st.form(f"close_{pos['position_id']}"):
                        exit_price = st.number_input(
                            "Exit Price",
                            min_value=0.01,
                            max_value=0.99,
                            value=float(pos['current_price']) if pos['current_price'] else 0.50,
                            step=0.01,
                            format="%.4f",
                        )
                        
                        if st.form_submit_button("Close Position"):
                            try:
                                client.close_position(pos['position_id'], exit_price)
                                st.success("Position closed successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to close position: {e}")
    else:
        st.info("No open positions")

with tab2:
    st.subheader("Closed Positions")
    
    try:
        positions = client.list_positions(status="closed")
    except Exception as e:
        st.error(f"Failed to fetch positions: {e}")
        positions = []
    
    if positions:
        st.dataframe(
            [
                {
                    "Market": pos["market_id"][:12] + "...",
                    "Side": pos["side"],
                    "Size": f"${pos['size']:,.0f}",
                    "Entry": f"{pos['entry_price']:.4f}",
                    "Realized P&L": f"${pos['realized_pnl']:,.2f}" if pos["realized_pnl"] else "N/A",
                    "P&L %": f"{(pos['realized_pnl']/pos['size']*100):.2f}%" if pos["realized_pnl"] and pos['size'] else "N/A",
                    "Zone": f"Z{pos['zone']}",
                    "Opened": pos["opened_at"][:10],
                    "Closed": pos["closed_at"][:10] if pos["closed_at"] else "N/A",
                }
                for pos in positions
            ],
            use_container_width=True,
        )
    else:
        st.info("No closed positions yet")
