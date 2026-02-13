"""API client for dashboard.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class APIClient:
    """HTTP client for PETS API."""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "") -> None:
        """Initialize API client.
        
        Args:
            base_url: Base URL for API
            api_key: API key for authentication
        """
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"X-API-Key": api_key} if api_key else {},
            timeout=30.0,
        )

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    # Bots endpoints
    async def list_bots(self) -> Dict[str, Any]:
        """Get list of bots.
        
        Returns:
            Response with bots list and total count
        """
        response = await self.client.get("/api/v1/bots")
        response.raise_for_status()
        return response.json()

    async def get_bot(self, bot_id: int) -> Dict[str, Any]:
        """Get bot details.
        
        Args:
            bot_id: Bot identifier
            
        Returns:
            Bot details
        """
        response = await self.client.get(f"/api/v1/bots/{bot_id}")
        response.raise_for_status()
        return response.json()

    async def start_bot(self, bot_id: int) -> Dict[str, Any]:
        """Start bot.
        
        Args:
            bot_id: Bot identifier
            
        Returns:
            Start operation response
        """
        response = await self.client.post(f"/api/v1/bots/{bot_id}/start")
        response.raise_for_status()
        return response.json()

    async def stop_bot(self, bot_id: int) -> Dict[str, Any]:
        """Stop bot.
        
        Args:
            bot_id: Bot identifier
            
        Returns:
            Stop operation response
        """
        response = await self.client.post(f"/api/v1/bots/{bot_id}/stop")
        response.raise_for_status()
        return response.json()

    async def pause_bot(self, bot_id: int) -> Dict[str, Any]:
        """Pause bot.
        
        Args:
            bot_id: Bot identifier
            
        Returns:
            Pause operation response
        """
        response = await self.client.post(f"/api/v1/bots/{bot_id}/pause")
        response.raise_for_status()
        return response.json()

    async def update_bot_config(self, bot_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update bot configuration.
        
        Args:
            bot_id: Bot identifier
            config: New configuration
            
        Returns:
            Updated bot details
        """
        response = await self.client.put(f"/api/v1/bots/{bot_id}/config", json={"config": config})
        response.raise_for_status()
        return response.json()

    # Positions endpoints
    async def list_positions(self, bot_id: Optional[int] = None) -> Dict[str, Any]:
        """Get list of positions.
        
        Args:
            bot_id: Optional bot filter
            
        Returns:
            Response with positions list
        """
        params = {"bot_id": bot_id} if bot_id else {}
        response = await self.client.get("/api/v1/positions", params=params)
        response.raise_for_status()
        return response.json()

    async def get_position(self, position_id: int) -> Dict[str, Any]:
        """Get position details.
        
        Args:
            position_id: Position identifier
            
        Returns:
            Position details
        """
        response = await self.client.get(f"/api/v1/positions/{position_id}")
        response.raise_for_status()
        return response.json()

    async def close_position(self, position_id: int) -> Dict[str, Any]:
        """Close position.
        
        Args:
            position_id: Position identifier
            
        Returns:
            Close operation response
        """
        response = await self.client.post(f"/api/v1/positions/{position_id}/close")
        response.raise_for_status()
        return response.json()

    # Orders endpoints
    async def list_orders(self, bot_id: Optional[int] = None) -> Dict[str, Any]:
        """Get list of orders.
        
        Args:
            bot_id: Optional bot filter
            
        Returns:
            Response with orders list
        """
        params = {"bot_id": bot_id} if bot_id else {}
        response = await self.client.get("/api/v1/orders", params=params)
        response.raise_for_status()
        return response.json()

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order details.
        
        Args:
            order_id: Order identifier
            
        Returns:
            Order details
        """
        response = await self.client.get(f"/api/v1/orders/{order_id}")
        response.raise_for_status()
        return response.json()

    async def place_order(
        self,
        market_id: str,
        side: str,
        size: float,
        price: float,
        bot_id: int,
    ) -> Dict[str, Any]:
        """Place new order.
        
        Args:
            market_id: Market identifier
            side: Order side (YES/NO)
            size: Order size
            price: Order price
            bot_id: Bot identifier
            
        Returns:
            Placed order details
        """
        payload = {
            "market_id": market_id,
            "side": side,
            "size": size,
            "price": price,
            "bot_id": bot_id,
        }
        response = await self.client.post("/api/v1/orders", json=payload)
        response.raise_for_status()
        return response.json()

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel order.
        
        Args:
            order_id: Order identifier
            
        Returns:
            Cancel operation response
        """
        response = await self.client.delete(f"/api/v1/orders/{order_id}")
        response.raise_for_status()
        return response.json()

    # Metrics endpoints
    async def get_bot_metrics(self, bot_id: int) -> Dict[str, Any]:
        """Get bot metrics.
        
        Args:
            bot_id: Bot identifier
            
        Returns:
            Bot metrics
        """
        response = await self.client.get(f"/api/v1/metrics/bots/{bot_id}")
        response.raise_for_status()
        return response.json()

    async def get_portfolio_metrics(self) -> Dict[str, Any]:
        """Get portfolio metrics.
        
        Returns:
            Portfolio metrics
        """
        response = await self.client.get("/api/v1/metrics/portfolio")
        response.raise_for_status()
        return response.json()

    # Wallet endpoints
    async def get_wallet_balance(self) -> Dict[str, Any]:
        """Get wallet balance.
        
        Returns:
            Wallet balance details
        """
        response = await self.client.get("/api/v1/wallet/balance")
        response.raise_for_status()
        return response.json()

    async def topup_wallet(self, amount: float) -> Dict[str, Any]:
        """Top up hot wallet.
        
        Args:
            amount: Amount to transfer from cold wallet
            
        Returns:
            Top-up operation response
        """
        response = await self.client.post("/api/v1/wallet/topup", json={"amount": amount})
        response.raise_for_status()
        return response.json()

    async def rebalance_wallet(self) -> Dict[str, Any]:
        """Rebalance hot wallet.
        
        Returns:
            Rebalance operation response
        """
        response = await self.client.post("/api/v1/wallet/rebalance")
        response.raise_for_status()
        return response.json()

    # Risk endpoints
    async def get_risk_metrics(self) -> Dict[str, Any]:
        """Get risk metrics.
        
        Returns:
            Risk metrics
        """
        response = await self.client.get("/api/v1/risk/metrics")
        response.raise_for_status()
        return response.json()

    async def get_circuit_breakers(self) -> Dict[str, Any]:
        """Get circuit breaker statuses.
        
        Returns:
            Circuit breaker statuses
        """
        response = await self.client.get("/api/v1/risk/circuit-breakers")
        response.raise_for_status()
        return response.json()

    async def emergency_halt(self) -> Dict[str, Any]:
        """Trigger emergency halt.
        
        Returns:
            Emergency halt response
        """
        response = await self.client.post("/api/v1/risk/emergency-halt")
        response.raise_for_status()
        return response.json()

    # Health endpoints
    async def check_health(self) -> Dict[str, Any]:
        """Check API health.
        
        Returns:
            Health status
        """
        response = await self.client.get("/api/v1/health/ready")
        response.raise_for_status()
        return response.json()
