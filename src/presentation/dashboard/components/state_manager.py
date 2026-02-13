"""Session state management.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import streamlit as st
from typing import Any, Optional


class StateManager:
    """Manage Streamlit session state.
    
    Examples:
        >>> state = StateManager()
        >>> state.set("api_client", client)
        >>> client = state.get("api_client")
    """

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get value from session state.
        
        Args:
            key: State key
            default: Default value if key not found
        
        Returns:
            State value or default
        """
        return st.session_state.get(key, default)

    @staticmethod
    def set(key: str, value: Any) -> None:
        """Set value in session state.
        
        Args:
            key: State key
            value: Value to store
        """
        st.session_state[key] = value

    @staticmethod
    def has(key: str) -> bool:
        """Check if key exists in session state.
        
        Args:
            key: State key
        
        Returns:
            True if key exists
        """
        return key in st.session_state

    @staticmethod
    def delete(key: str) -> None:
        """Delete key from session state.
        
        Args:
            key: State key
        """
        if key in st.session_state:
            del st.session_state[key]
