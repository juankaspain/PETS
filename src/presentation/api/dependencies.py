"""FastAPI dependencies for dependency injection."""

import logging
from typing import Annotated

from fastapi import Depends

from src.domain.services.kelly_calculator import KellyCalculator
from src.domain.services.pnl_calculator import PnLCalculator
from src.domain.services.risk_calculator import RiskCalculator
from src.domain.services.zone_classifier import ZoneClassifier
from src.infrastructure.persistence.redis_client import RedisClient
from src.infrastructure.persistence.timescaledb import TimescaleDBClient

logger = logging.getLogger(__name__)


# Database clients (singleton pattern)
_timescale_client: TimescaleDBClient | None = None
_redis_client: RedisClient | None = None


async def get_timescale_client() -> TimescaleDBClient:
    """Get TimescaleDB client (singleton)."""
    global _timescale_client
    if _timescale_client is None:
        _timescale_client = TimescaleDBClient(
            host="localhost",
            port=5432,
            database="pets",
            user="pets",
            password="pets_password",
        )
        await _timescale_client.connect()
    return _timescale_client


async def get_redis_client() -> RedisClient:
    """Get Redis client (singleton)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient(
            host="localhost",
            port=6379,
            db=0,
        )
        await _redis_client.connect()
    return _redis_client


# Services (stateless, can create new instances)
def get_risk_calculator() -> RiskCalculator:
    """Get risk calculator."""
    return RiskCalculator()


def get_kelly_calculator() -> KellyCalculator:
    """Get Kelly calculator."""
    return KellyCalculator()


def get_zone_classifier() -> ZoneClassifier:
    """Get zone classifier."""
    return ZoneClassifier()


def get_pnl_calculator() -> PnLCalculator:
    """Get P&L calculator."""
    return PnLCalculator()


# Type aliases for dependency injection
TimescaleDB = Annotated[TimescaleDBClient, Depends(get_timescale_client)]
Redis = Annotated[RedisClient, Depends(get_redis_client)]
RiskCalc = Annotated[RiskCalculator, Depends(get_risk_calculator)]
KellyCalc = Annotated[KellyCalculator, Depends(get_kelly_calculator)]
ZoneClass = Annotated[ZoneClassifier, Depends(get_zone_classifier)]
PnLCalc = Annotated[PnLCalculator, Depends(get_pnl_calculator)]
