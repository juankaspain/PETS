"""API client for FastAPI backend."""

import requests
from typing import Any, Literal


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

    def _request(
        self,
        method: Literal["GET", "POST", "PUT", "DELETE"],
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict | list | None:
        """Make HTTP request to API.

        Args:
            method: HTTP method
            endpoint: API endpoint (e.g., '/api/bots')
            params: Query parameters
            json: JSON body

        Returns:
            Response JSON or None for 204

        Raises:
            requests.HTTPError: On HTTP error
        """
        url = f"{self.base_url}{endpoint}"
        
        response = self.session.request(
            method=method,
            url=url,
            params=params,
            json=json,
        )
        
        response.raise_for_status()
        
        # 204 No Content returns None
        if response.status_code == 204:
            return None
        
        return response.json()

    def health_check(self) -> dict:
        """Health check."""
        return self._request("GET", "/health")

    # Bots
    def create_bot(self, strategy_type: str, config: dict, capital_allocated: float) -> dict:
        """Create bot."""
        return self._request(
            "POST",
            "/api/bots",
            json={
                "strategy_type": strategy_type,
                "config": config,
                "capital_allocated": capital_allocated,
            },
        )

    def list_bots(self, limit: int = 100) -> list[dict]:
        """List bots."""
        return self._request(
            "GET",
            "/api/bots",
            params={"limit": limit},
        )

    def get_bot(self, bot_id: int) -> dict:
        """Get bot."""
        return self._request("GET", f"/api/bots/{bot_id}")

    def update_bot_state(self, bot_id: int, state: str) -> dict:
        """Update bot state."""
        return self._request(
            "PUT",
            f"/api/bots/{bot_id}/state",
            json={"state": state},
        )

    def delete_bot(self, bot_id: int) -> None:
        """Delete bot."""
        return self._request("DELETE", f"/api/bots/{bot_id}")

    # Orders
    def list_orders(
        self,
        bot_id: int | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """List orders."""
        params = {"limit": limit}
        if bot_id:
            params["bot_id"] = bot_id
        if status:
            params["status"] = status

        return self._request("GET", "/api/orders", params=params)

    # Positions
    def list_positions(
        self,
        bot_id: int | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """List positions."""
        params = {"limit": limit}
        if bot_id:
            params["bot_id"] = bot_id
        if status:
            params["status"] = status

        return self._request("GET", "/api/positions", params=params)

    def close_position(self, position_id: str, exit_price: float) -> dict:
        """Close position."""
        return self._request(
            "PUT",
            f"/api/positions/{position_id}/close",
            json={"exit_price": exit_price},
        )

    # Markets
    def list_markets(
        self,
        active: bool = True,
        min_liquidity: float | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """List markets."""
        params = {"active": active, "limit": limit}
        if min_liquidity:
            params["min_liquidity"] = min_liquidity

        return self._request("GET", "/api/markets", params=params)

    # Analytics
    def get_portfolio_metrics(self) -> dict:
        """Get portfolio metrics."""
        return self._request("GET", "/api/analytics/portfolio")

    def get_performance_metrics(self) -> dict:
        """Get performance metrics."""
        return self._request("GET", "/api/analytics/performance")

    def get_risk_metrics(self) -> dict:
        """Get risk metrics."""
        return self._request("GET", "/api/analytics/risk")

    # Paper Trading (placeholder for Fase 6)
    def get_paper_wallet(self) -> dict:
        """Get paper trading wallet."""
        return self._request("GET", "/api/paper/wallet")

    def reset_paper_wallet(self, initial_balance: float = 10000) -> dict:
        """Reset paper trading wallet."""
        return self._request(
            "POST",
            "/api/paper/wallet/reset",
            json={"initial_balance": initial_balance},
        )

    def get_paper_positions(self, status: str | None = None) -> list[dict]:
        """Get paper trading positions."""
        params = {}
        if status:
            params["status"] = status
        return self._request("GET", "/api/paper/positions", params=params)

    def get_paper_metrics(self) -> dict:
        """Get paper trading metrics."""
        return self._request("GET", "/api/paper/metrics")
