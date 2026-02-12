"""Plotly charts for dashboard."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_equity_curve(data: list[dict]) -> go.Figure:
    """Create equity curve chart.

    Args:
        data: List of {date, value} dicts

    Returns:
        Plotly figure
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=[d["date"] for d in data],
            y=[d["value"] for d in data],
            mode="lines+markers",
            name="Portfolio Value",
            line=dict(color="#00d4aa", width=2),
            marker=dict(size=6),
        )
    )

    fig.update_layout(
        title="Equity Curve",
        xaxis_title="Date",
        yaxis_title="Value ($)",
        hovermode="x unified",
        template="plotly_dark",
    )

    return fig


def create_pnl_chart(data: list[dict]) -> go.Figure:
    """Create daily P&L bar chart.

    Args:
        data: List of {date, pnl} dicts

    Returns:
        Plotly figure
    """
    colors = ["#00d4aa" if d["pnl"] >= 0 else "#ff4b4b" for d in data]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=[d["date"] for d in data],
            y=[d["pnl"] for d in data],
            name="Daily P&L",
            marker_color=colors,
        )
    )

    fig.update_layout(
        title="Daily P&L",
        xaxis_title="Date",
        yaxis_title="P&L ($)",
        hovermode="x unified",
        template="plotly_dark",
    )

    return fig


def create_zone_exposure_chart(zone_exposure: dict[str, float]) -> go.Figure:
    """Create zone exposure pie chart.

    Args:
        zone_exposure: Dict of zone -> exposure

    Returns:
        Plotly figure
    """
    fig = go.Figure()

    fig.add_trace(
        go.Pie(
            labels=list(zone_exposure.keys()),
            values=list(zone_exposure.values()),
            hole=0.3,
            marker=dict(
                colors=["#00d4aa", "#4da6ff", "#ffaa00", "#ff4b4b", "#8b0000"]
            ),
        )
    )

    fig.update_layout(
        title="Zone Exposure",
        template="plotly_dark",
    )

    return fig
