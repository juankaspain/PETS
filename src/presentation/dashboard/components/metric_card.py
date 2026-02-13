"""Reusable metric card component.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import streamlit as st
from typing import Optional


def render_metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_color: str = "normal",
) -> None:
    """Render metric card with optional delta.
    
    Args:
        label: Metric label
        value: Current metric value
        delta: Change value (optional)
        delta_color: Color for delta ("normal", "inverse", "off")
    
    Examples:
        >>> render_metric_card("Portfolio Value", "$12,345", "+$234", "normal")
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color,
    )
