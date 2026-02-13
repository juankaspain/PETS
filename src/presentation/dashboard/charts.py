"""Chart generation utilities using Plotly.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from typing import Any, Dict, List

import plotly.graph_objects as go
import streamlit as st


@st.cache_data(ttl=60)
def roi_chart(data: List[Dict[str, Any]]) -> go.Figure:
    """Create ROI time series chart.
    
    Args:
        data: List of dicts with 'timestamp' and 'roi' keys
    
    Returns:
        Plotly Figure object
    
    Examples:
        >>> data = [
        ...     {"timestamp": "2026-02-13T00:00:00", "roi": 0.05},
        ...     {"timestamp": "2026-02-13T01:00:00", "roi": 0.07},
        ... ]
        >>> fig = roi_chart(data)
    """
    timestamps = [d["timestamp"] for d in data]
    rois = [d["roi"] * 100 for d in data]  # Convert to percentage
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=rois,
            mode="lines+markers",
            name="ROI",
            line=dict(color="#00d4aa", width=2),
            marker=dict(size=6),
        )
    )
    
    fig.update_layout(
        title="ROI Over Time",
        xaxis_title="Timestamp",
        yaxis_title="ROI (%)",
        hovermode="x unified",
        template="plotly_dark",
    )
    
    return fig


@st.cache_data(ttl=60)
def drawdown_chart(data: List[Dict[str, Any]]) -> go.Figure:
    """Create underwater drawdown chart.
    
    Args:
        data: List of dicts with 'timestamp' and 'drawdown' keys
    
    Returns:
        Plotly Figure object
    """
    timestamps = [d["timestamp"] for d in data]
    drawdowns = [d["drawdown"] * 100 for d in data]  # Convert to percentage
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=drawdowns,
            mode="lines",
            name="Drawdown",
            fill="tozeroy",
            line=dict(color="#ff4444", width=2),
        )
    )
    
    fig.update_layout(
        title="Drawdown (Underwater Plot)",
        xaxis_title="Timestamp",
        yaxis_title="Drawdown (%)",
        hovermode="x unified",
        template="plotly_dark",
    )
    
    return fig


@st.cache_data(ttl=60)
def exposure_heatmap(data: List[Dict[str, Any]]) -> go.Figure:
    """Create risk zone exposure heatmap.
    
    Args:
        data: List of dicts with 'bot_id' and 'zone_X' exposure values
    
    Returns:
        Plotly Figure object
    """
    bot_ids = [d["bot_id"] for d in data]
    zones = ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5"]
    
    # Build exposure matrix
    exposure_matrix = []
    for zone_idx in range(1, 6):
        row = [d.get(f"zone_{zone_idx}", 0) for d in data]
        exposure_matrix.append(row)
    
    fig = go.Figure(
        data=go.Heatmap(
            z=exposure_matrix,
            x=bot_ids,
            y=zones,
            colorscale=[
                [0, "green"],
                [0.5, "orange"],
                [1, "red"],
            ],
            hovertemplate="Bot %{x}<br>%{y}: %{z}%<extra></extra>",
        )
    )
    
    fig.update_layout(
        title="Risk Zone Exposure by Bot",
        xaxis_title="Bot ID",
        yaxis_title="Risk Zone",
        template="plotly_dark",
    )
    
    return fig


@st.cache_data(ttl=60)
def pnl_distribution(data: List[float]) -> go.Figure:
    """Create P&L distribution histogram.
    
    Args:
        data: List of P&L values
    
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    
    fig.add_trace(
        go.Histogram(
            x=data,
            nbinsx=30,
            marker=dict(
                color="#00d4aa",
                line=dict(color="white", width=1),
            ),
            name="P&L",
        )
    )
    
    fig.update_layout(
        title="P&L Distribution",
        xaxis_title="P&L ($)",
        yaxis_title="Frequency",
        template="plotly_dark",
    )
    
    return fig
