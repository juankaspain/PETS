"""Metric card component.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from typing import Optional

import streamlit as st


def metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_color: str = "normal",
) -> None:
    """Display metric card.
    
    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta value
        delta_color: Delta color (normal/inverse/off)
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color,
    )
