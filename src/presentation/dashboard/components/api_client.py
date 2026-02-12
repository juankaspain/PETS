"""API client for FastAPI backend."""

import requests
from typing import Any


class APIClient:
    """HTTP client for PETS FastAPI backend."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize API client.

        Args:
            base_url: Base URL for FastAPI backend
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def health_check(self) -> dict:
        """Health check."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    # Bots
    def create_bot(self, strategy_type: str, config: dict, capital_allocated: float) -> dict:
        """Create bot."""
        response = self.session.post(
            f"{self.base_url}/api/bots",
            json={
                "strategy_type": strategy_type,
                "config": config,
                "capital_allocated": capital_allocated,
            },
        )
        response.raise_for_status()
        return response.json()

    def list_bots(self, limit: int = 100) -> list[dict]:
        """List bots."""
        response = self.session.get(
            f"{self.base_url}/api/bots",
            params={"limit": limit},
        )
        response.raise_for_status()
        return response.json()

    def get_bot(self, bot_id: int) -> dict:
        """Get bot."""
        response = self.session.get(f"{self.base_url}/api/bots/{bot_id}")
        response.raise_for_status()
        return response.json()

    def update_bot_state(self, bot_id: int, state: str) -> dict:
        """Update bot state."""
        response = self.session.put(
            f"{self.base_url}/api/bots/{bot_id}/state",
            json={"state": state},
        )
        response.raise_for_status()
        return response.json()

    def delete_bot(self, bot_id: int) -> None:
        """Delete bot."""
        response = self.session.delete(f"{self.base_url}/api/bots/{bot_id}")
        response.raise_for_status()

    # Orders
    def list_orders(self, bot_id: int | None = None, status: str | None = None, limit: int = 100) -> list[dict]:
        """List orders."""
        params = {"limit": limit}
        if bot_id:
            params["bot_id"] = bot_id
        if status:
            params["status"] = status

        response = self.session.get(
            f"{self.base_url}/api/orders",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    # Positions
    def list_positions(self, bot_id: int | None = None, status: str | None = None, limit: int = 100) -> list[dict]:
        """List positions."""
        params = {"limit": limit}
        if bot_id:
            params["bot_id"] = bot_id
        if status:
            params["status"] = status

        response = self.session.get(
            f"{self.base_url}/api/positions",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def close_position(self, position_id: str, exit_price: float) -> dict:
        """Close position."""
        response = self.session.put(
            f"{self.base_url}/api/positions/{position_id}/close",
            json={"exit_price": exit_price},
        )
        response.raise_for_status()
        return response.json()

    # Markets
    def list_markets(self, active: bool = True, min_liquidity: float | None = None, limit: int = 100) -> list[dict]:
        """List markets."""
        params = {"active": active, "limit": limit}
        if min_liquidity:
            params["min_liquidity"] = min_liquidity

        response = self.session.get(
            f"{self.base_url}/api/markets",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    # Analytics
    def get_portfolio_metrics(self) -> dict:
        """Get portfolio metrics."""
        response = self.session.get(f"{self.base_url}/api/analytics/portfolio")
        response.raise_for_status()
        return response.json()

    def get_performance_metrics(self) -> dict:
        """Get performance metrics."""
        response = self.session.get(f"{self.base_url}/api/analytics/performance")
        response.raise_for_status()
        return response.json()

    def get_risk_metrics(self) -> dict:
        """Get risk metrics."""
        response = self.session.get(f"{self.base_url}/api/analytics/risk")
        response.raise_for_status()
        return response.json()
