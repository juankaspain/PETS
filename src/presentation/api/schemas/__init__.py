"""API Schemas (Pydantic models)."""

from src.presentation.api.schemas.bot import (
    BotConfigUpdate,
    BotListResponse,
    BotResponse,
)
from src.presentation.api.schemas.health import (
    HealthResponse,
    ReadinessResponse,
    StartupResponse,
)
from src.presentation.api.schemas.metrics import (
    BotMetrics,
    PortfolioMetrics,
    PrometheusMetrics,
)
from src.presentation.api.schemas.order import (
    OrderListResponse,
    OrderResponse,
    PlaceOrderRequest,
)
from src.presentation.api.schemas.position import (
    ClosePositionRequest,
    PositionListResponse,
    PositionResponse,
)
from src.presentation.api.schemas.risk import (
    CircuitBreakerStatus,
    EmergencyHaltRequest,
    RiskMetrics,
)
from src.presentation.api.schemas.wallet import (
    RebalanceWalletRequest,
    TopUpWalletRequest,
    TransactionResponse,
    WalletBalanceResponse,
)

__all__ = [
    # Bot
    "BotResponse",
    "BotListResponse",
    "BotConfigUpdate",
    # Position
    "PositionResponse",
    "PositionListResponse",
    "ClosePositionRequest",
    # Order
    "OrderResponse",
    "OrderListResponse",
    "PlaceOrderRequest",
    # Metrics
    "BotMetrics",
    "PortfolioMetrics",
    "PrometheusMetrics",
    # Health
    "HealthResponse",
    "ReadinessResponse",
    "StartupResponse",
    # Wallet
    "WalletBalanceResponse",
    "TopUpWalletRequest",
    "RebalanceWalletRequest",
    "TransactionResponse",
    # Risk
    "RiskMetrics",
    "CircuitBreakerStatus",
    "EmergencyHaltRequest",
]
