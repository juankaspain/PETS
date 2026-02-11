"""SQLAlchemy models for PETS database.

Defines ORM models for all domain entities.
Uses TimescaleDB hypertables for time-series data.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    DateTime,
    Boolean,
    JSON,
    ForeignKey,
    Index,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class BotModel(Base):
    """Bot entity ORM model."""

    __tablename__ = "bots"

    bot_id = Column(Integer, primary_key=True)
    strategy_type = Column(String(50), nullable=False)
    state = Column(String(20), nullable=False, default="IDLE")
    config = Column(JSON, nullable=False)
    capital_allocated = Column(Numeric(20, 6), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    orders = relationship("OrderModel", back_populates="bot", cascade="all, delete-orphan")
    positions = relationship(
        "PositionModel", back_populates="bot", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_bots_state", "state"),
        Index("idx_bots_strategy_type", "strategy_type"),
    )


class OrderModel(Base):
    """Order entity ORM model."""

    __tablename__ = "orders"

    order_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(Integer, ForeignKey("bots.bot_id", ondelete="CASCADE"), nullable=False)
    market_id = Column(String(66), nullable=False)  # 0x + 64 hex chars
    side = Column(String(3), nullable=False)  # YES or NO
    size = Column(Numeric(20, 6), nullable=False)
    price = Column(Numeric(6, 4), nullable=False)  # 0.01 to 0.99
    zone = Column(Integer, nullable=False)  # 1-5
    status = Column(String(20), nullable=False, default="PENDING")
    post_only = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    bot = relationship("BotModel", back_populates="orders")
    trades = relationship("TradeModel", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_orders_bot_created", "bot_id", "created_at"),
        Index("idx_orders_market_created", "market_id", "created_at"),
        Index("idx_orders_status_created", "status", "created_at"),
        Index("idx_orders_zone_created", "zone", "created_at"),
    )


class PositionModel(Base):
    """Position entity ORM model."""

    __tablename__ = "positions"

    position_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(Integer, ForeignKey("bots.bot_id", ondelete="CASCADE"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=False)
    market_id = Column(String(66), nullable=False)
    side = Column(String(3), nullable=False)  # YES or NO
    size = Column(Numeric(20, 6), nullable=False)
    entry_price = Column(Numeric(6, 4), nullable=False)
    current_price = Column(Numeric(6, 4), nullable=True)
    realized_pnl = Column(Numeric(20, 6), nullable=True)
    unrealized_pnl = Column(Numeric(20, 6), nullable=True)
    zone = Column(Integer, nullable=False)  # 1-5
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    bot = relationship("BotModel", back_populates="positions")

    __table_args__ = (
        Index(
            "idx_positions_bot_open",
            "bot_id",
            "opened_at",
            postgresql_where=(closed_at == None),
        ),
        Index("idx_positions_bot_closed", "bot_id", "closed_at"),
        Index("idx_positions_market", "market_id"),
    )


class TradeModel(Base):
    """Trade entity ORM model."""

    __tablename__ = "trades"

    trade_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=False)
    executed_price = Column(Numeric(6, 4), nullable=False)
    executed_size = Column(Numeric(20, 6), nullable=False)
    fees_paid = Column(Numeric(20, 6), nullable=False, default=Decimal("0"))
    slippage = Column(Numeric(6, 4), nullable=False, default=Decimal("0"))
    gas_cost_usdc = Column(Numeric(20, 6), nullable=True)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    order = relationship("OrderModel", back_populates="trades")

    __table_args__ = (
        Index("idx_trades_order_executed", "order_id", "executed_at"),
        Index("idx_trades_executed", "executed_at"),
    )


class MarketModel(Base):
    """Market entity ORM model."""

    __tablename__ = "markets"

    market_id = Column(String(66), primary_key=True)  # 0x + 64 hex chars
    question = Column(Text, nullable=False)
    outcomes = Column(JSON, nullable=False)  # List of outcome names
    liquidity = Column(Numeric(20, 6), nullable=False, default=Decimal("0"))
    volume_24h = Column(Numeric(20, 6), nullable=False, default=Decimal("0"))
    yes_price = Column(Numeric(6, 4), nullable=True)
    no_price = Column(Numeric(6, 4), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolves_at = Column(DateTime(timezone=True), nullable=True)
    resolved = Column(Boolean, nullable=False, default=False)
    resolved_outcome = Column(String(10), nullable=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_markets_resolved", "resolved"),
        Index("idx_markets_resolves_at", "resolves_at"),
    )


class WalletModel(Base):
    """Wallet entity ORM model."""

    __tablename__ = "wallets"

    address = Column(String(42), primary_key=True)  # 0x + 40 hex chars
    balance_usdc = Column(Numeric(20, 6), nullable=False, default=Decimal("0"))
    balance_matic = Column(Numeric(20, 18), nullable=False, default=Decimal("0"))
    nonce = Column(Integer, nullable=False, default=0)
    last_sync_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (Index("idx_wallets_last_sync", "last_sync_at"),)


class MarketSnapshotModel(Base):
    """Market snapshot for time-series data (hypertable)."""

    __tablename__ = "market_snapshots"

    snapshot_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    market_id = Column(String(66), nullable=False)
    yes_price = Column(Numeric(6, 4), nullable=False)
    no_price = Column(Numeric(6, 4), nullable=False)
    liquidity = Column(Numeric(20, 6), nullable=False)
    volume = Column(Numeric(20, 6), nullable=False)
    snapshot_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_market_snapshots_market_time", "market_id", "snapshot_at"),
    )
