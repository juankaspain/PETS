"""API client for backend communication.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import requests
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class APIClient:
    """HTTP client for PETS backend API.
    
    Examples:
        >>> client = APIClient(base_url="http://localhost:8000")
        >>> metrics = client.get_portfolio_metrics()
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize API client.
        
        Args:
            base_url: Backend API base URL
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers["X-API-Key"] = api_key

    def get_portfolio_metrics(self) -> Dict[str, Any]:
        """Get portfolio-level metrics.
        
        Returns:
            Portfolio metrics dictionary
        """
        try:
            response = self.session.get(f"{self.base_url}/api/v1/metrics/portfolio")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch portfolio metrics: {e}")
            return self._get_default_metrics()

    def get_bot_list(self) -> List[Dict[str, Any]]:
        """Get list of all bots.
        
        Returns:
            List of bot dictionaries
        """
        try:
            response = self.session.get(f"{self.base_url}/api/v1/bots")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch bot list: {e}")
            return []

    def get_bot_metrics(self, bot_id: int) -> Dict[str, Any]:
        """Get metrics for specific bot.
        
        Args:
            bot_id: Bot ID
        
        Returns:
            Bot metrics dictionary
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/metrics/bots/{bot_id}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch bot {bot_id} metrics: {e}")
            return {}

    def emergency_halt(self) -> Dict[str, str]:
        """Trigger emergency halt for all bots.
        
        Returns:
            Status response
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/risk/emergency-halt"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to trigger emergency halt: {e}")
            return {"status": "error", "message": str(e)}

    def _get_default_metrics(self) -> Dict[str, Any]:
        """Get default metrics when API unavailable.
        
        Returns:
            Default metrics dictionary
        """
        return {
            "portfolio_value": 0.0,
            "total_pnl": 0.0,
            "open_positions": 0,
            "active_bots": 0,
        }
