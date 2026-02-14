"""Domain Events for the PETS trading system.

This module implements the Event-Driven Architecture pattern with:
- Base DomainEvent class for all events
- Trading-specific events (OrderFilled, PositionClosed, etc.)
- Event metadata and serialization
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from enum import Enum


class EventType(str, Enum):
    """Types of domain events."""
    ORDER_PLACED = "order.placed"
    ORDER_FILLED = "order.filled"
    ORDER_CANCELLED = "order.cancelled"
    ORDER_REJECTED = "order.rejected"
    POSITION_OPENED = "position.opened"
    POSITION_CLOSED = "position.closed"
    POSITION_UPDATED = "position.updated"
    BOT_STARTED = "bot.started"
    BOT_STOPPED = "bot.stopped"
    BOT_ERROR = "bot.error"
    MARKET_DATA_RECEIVED = "market.data_received"
    CIRCUIT_BREAKER_TRIGGERED = "circuit_breaker.triggered"


@dataclass
class DomainEvent:
    """Base class for all domain events.
    
    All events carry metadata including:
    - Unique event ID
    - Timestamp of when event occurred
    - Event type for routing
    - Optional correlation ID for tracing
    
    Example:
        event = OrderFilledEvent(
            order_id="123",
            fill_price=0.55,
            fill_amount=100.0
        )
        publish(event)
    """
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_type: EventType = field(default=EventType.ORDER_PLACED)
    correlation_id: Optional[UUID] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary."""
        return {
            "event_id": str(self.event_id),
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "correlation_id": str(self.correlation_id) if self.correlation_id else None,
        }


@dataclass
class OrderFilledEvent(DomainEvent):
    """Event emitted when an order is filled."""
    order_id: str = ""
    market_id: str = ""
    bot_id: int = 0
    side: str = ""  # "BUY" or "SELL"
    fill_price: float = 0.0
    fill_amount: float = 0.0
    fee: float = 0.0
    event_type: EventType = field(default=EventType.ORDER_FILLED)
    
    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "order_id": self.order_id,
            "market_id": self.market_id,
            "bot_id": self.bot_id,
            "side": self.side,
            "fill_price": self.fill_price,
            "fill_amount": self.fill_amount,
            "fee": self.fee,
        })
        return base


@dataclass
class PositionClosedEvent(DomainEvent):
    """Event emitted when a position is closed."""
    position_id: str = ""
    market_id: str = ""
    bot_id: int = 0
    entry_price: float = 0.0
    exit_price: float = 0.0
    pnl: float = 0.0
    pnl_percent: float = 0.0
    holding_time_seconds: int = 0
    event_type: EventType = field(default=EventType.POSITION_CLOSED)
    
    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "position_id": self.position_id,
            "market_id": self.market_id,
            "bot_id": self.bot_id,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "pnl": self.pnl,
            "pnl_percent": self.pnl_percent,
            "holding_time_seconds": self.holding_time_seconds,
        })
        return base


@dataclass
class BotErrorEvent(DomainEvent):
    """Event emitted when a bot encounters an error."""
    bot_id: int = 0
    error_type: str = ""
    error_message: str = ""
    stack_trace: Optional[str] = None
    recoverable: bool = True
    event_type: EventType = field(default=EventType.BOT_ERROR)


@dataclass 
class CircuitBreakerEvent(DomainEvent):
    """Event emitted when circuit breaker is triggered."""
    bot_id: int = 0
    reason: str = ""
    threshold_value: float = 0.0
    actual_value: float = 0.0
    cooldown_seconds: int = 300
    event_type: EventType = field(default=EventType.CIRCUIT_BREAKER_TRIGGERED)


# Export all event classes
__all__ = [
    "EventType",
    "DomainEvent",
    "OrderFilledEvent",
    "PositionClosedEvent",
    "BotErrorEvent",
    "CircuitBreakerEvent",
]
