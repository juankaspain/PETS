"""Common chart utilities and configurations.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import plotly.graph_objects as go
from typing import Dict, List, Any


def get_default_layout() -> Dict[str, Any]:
    """Get default Plotly layout configuration.
    
    Returns:
        Layout dictionary
    """
    return {
        "template": "plotly_white",
        "margin": dict(l=20, r=20, t=40, b=20),
        "height": 400,
        "hovermode": "x unified",
    }


def create_line_chart(
    x: List,
    y: List,
    title: str,
    x_label: str = "Time",
    y_label: str = "Value",
) -> go.Figure:
    """Create line chart with default styling.
    
    Args:
        x: X-axis data
        y: Y-axis data
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            name=y_label,
            line=dict(color="#1f77b4", width=2),
        )
    )
    
    layout = get_default_layout()
    layout.update({
        "title": title,
        "xaxis_title": x_label,
        "yaxis_title": y_label,
    })
    
    fig.update_layout(**layout)
    
    return fig


def create_pie_chart(
    labels: List[str],
    values: List[float],
    title: str,
) -> go.Figure:
    """Create pie chart with default styling.
    
    Args:
        labels: Slice labels
        values: Slice values
        title: Chart title
    
    Returns:
        Plotly figure
    """
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
            )
        ]
    )
    
    layout = get_default_layout()
    layout.update({"title": title})
    
    fig.update_layout(**layout)
    
    return fig


def create_heatmap(
    z: List[List[float]],
    x: List[str],
    y: List[str],
    title: str,
) -> go.Figure:
    """Create heatmap with default styling.
    
    Args:
        z: 2D array of values
        x: X-axis labels
        y: Y-axis labels
        title: Chart title
    
    Returns:
        Plotly figure
    """
    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=x,
            y=y,
            colorscale="Blues",
        )
    )
    
    layout = get_default_layout()
    layout.update({"title": title})
    
    fig.update_layout(**layout)
    
    return fig
