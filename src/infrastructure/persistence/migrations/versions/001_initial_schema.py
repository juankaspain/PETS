"""Initial schema.

Revision ID: 001
Revises:
Create Date: 2026-02-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema."""
    # Bots table
    op.create_table(
        "bots",
        sa.Column("bot_id", sa.Integer(), nullable=False),
        sa.Column("strategy_type", sa.String(length=50), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False, server_default="IDLE"),
        sa.Column("config", JSON(), nullable=False),
        sa.Column("capital_allocated", sa.Numeric(20, 6), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("bot_id"),
    )
    op.create_index("idx_bots_state", "bots", ["state"])
    op.create_index("idx_bots_strategy_type", "bots", ["strategy_type"])

    # Orders table
    op.create_table(
        "orders",
        sa.Column("order_id", UUID(as_uuid=True), nullable=False),
        sa.Column("bot_id", sa.Integer(), nullable=False),
        sa.Column("market_id", sa.String(length=66), nullable=False),
        sa.Column("side", sa.String(length=3), nullable=False),
        sa.Column("size", sa.Numeric(20, 6), nullable=False),
        sa.Column("price", sa.Numeric(6, 4), nullable=False),
        sa.Column("zone", sa.Integer(), nullable=False),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="PENDING"
        ),
        sa.Column("post_only", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["bot_id"], ["bots.bot_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("order_id"),
    )
    op.create_index(
        "idx_orders_bot_created", "orders", ["bot_id", "created_at"]
    )
    op.create_index(
        "idx_orders_market_created", "orders", ["market_id", "created_at"]
    )
    op.create_index(
        "idx_orders_status_created", "orders", ["status", "created_at"]
    )
    op.create_index(
        "idx_orders_zone_created", "orders", ["zone", "created_at"]
    )

    # Positions table
    op.create_table(
        "positions",
        sa.Column("position_id", UUID(as_uuid=True), nullable=False),
        sa.Column("bot_id", sa.Integer(), nullable=False),
        sa.Column("order_id", UUID(as_uuid=True), nullable=False),
        sa.Column("market_id", sa.String(length=66), nullable=False),
        sa.Column("side", sa.String(length=3), nullable=False),
        sa.Column("size", sa.Numeric(20, 6), nullable=False),
        sa.Column("entry_price", sa.Numeric(6, 4), nullable=False),
        sa.Column("current_price", sa.Numeric(6, 4), nullable=True),
        sa.Column("realized_pnl", sa.Numeric(20, 6), nullable=True),
        sa.Column("unrealized_pnl", sa.Numeric(20, 6), nullable=True),
        sa.Column("zone", sa.Integer(), nullable=False),
        sa.Column(
            "opened_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["bot_id"], ["bots.bot_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.order_id"]),
        sa.PrimaryKeyConstraint("position_id"),
    )
    op.create_index(
        "idx_positions_bot_open",
        "positions",
        ["bot_id", "opened_at"],
        postgresql_where=sa.text("closed_at IS NULL"),
    )
    op.create_index(
        "idx_positions_bot_closed", "positions", ["bot_id", "closed_at"]
    )
    op.create_index("idx_positions_market", "positions", ["market_id"])

    # Trades table
    op.create_table(
        "trades",
        sa.Column("trade_id", UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", UUID(as_uuid=True), nullable=False),
        sa.Column("executed_price", sa.Numeric(6, 4), nullable=False),
        sa.Column("executed_size", sa.Numeric(20, 6), nullable=False),
        sa.Column("fees_paid", sa.Numeric(20, 6), nullable=False, server_default="0"),
        sa.Column("slippage", sa.Numeric(6, 4), nullable=False, server_default="0"),
        sa.Column("gas_cost_usdc", sa.Numeric(20, 6), nullable=True),
        sa.Column(
            "executed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.order_id"]),
        sa.PrimaryKeyConstraint("trade_id"),
    )
    op.create_index(
        "idx_trades_order_executed", "trades", ["order_id", "executed_at"]
    )
    op.create_index("idx_trades_executed", "trades", ["executed_at"])

    # Markets table
    op.create_table(
        "markets",
        sa.Column("market_id", sa.String(length=66), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("outcomes", JSON(), nullable=False),
        sa.Column(
            "liquidity", sa.Numeric(20, 6), nullable=False, server_default="0"
        ),
        sa.Column(
            "volume_24h", sa.Numeric(20, 6), nullable=False, server_default="0"
        ),
        sa.Column("yes_price", sa.Numeric(6, 4), nullable=True),
        sa.Column("no_price", sa.Numeric(6, 4), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolves_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resolved_outcome", sa.String(length=10), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("market_id"),
    )
    op.create_index("idx_markets_resolved", "markets", ["resolved"])
    op.create_index("idx_markets_resolves_at", "markets", ["resolves_at"])

    # Wallets table
    op.create_table(
        "wallets",
        sa.Column("address", sa.String(length=42), nullable=False),
        sa.Column(
            "balance_usdc", sa.Numeric(20, 6), nullable=False, server_default="0"
        ),
        sa.Column(
            "balance_matic", sa.Numeric(20, 18), nullable=False, server_default="0"
        ),
        sa.Column("nonce", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "last_sync_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("address"),
    )
    op.create_index("idx_wallets_last_sync", "wallets", ["last_sync_at"])

    # Market snapshots table (will be hypertable)
    op.create_table(
        "market_snapshots",
        sa.Column("snapshot_id", UUID(as_uuid=True), nullable=False),
        sa.Column("market_id", sa.String(length=66), nullable=False),
        sa.Column("yes_price", sa.Numeric(6, 4), nullable=False),
        sa.Column("no_price", sa.Numeric(6, 4), nullable=False),
        sa.Column("liquidity", sa.Numeric(20, 6), nullable=False),
        sa.Column("volume", sa.Numeric(20, 6), nullable=False),
        sa.Column(
            "snapshot_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("snapshot_id"),
    )
    op.create_index(
        "idx_market_snapshots_market_time",
        "market_snapshots",
        ["market_id", "snapshot_at"],
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("market_snapshots")
    op.drop_table("wallets")
    op.drop_table("markets")
    op.drop_table("trades")
    op.drop_table("positions")
    op.drop_table("orders")
    op.drop_table("bots")
