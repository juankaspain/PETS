-- TimescaleDB initialization script
-- Creates hypertables, compression policies, and continuous aggregates

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Wait for tables to be created by Alembic
-- This script runs after migrations

-- Create hypertables
-- Orders hypertable (7-day chunks)
SELECT create_hypertable(
    'orders',
    'created_at',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Positions hypertable (7-day chunks)
SELECT create_hypertable(
    'positions',
    'opened_at',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Trades hypertable (7-day chunks)
SELECT create_hypertable(
    'trades',
    'executed_at',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Market snapshots hypertable (1-day chunks)
SELECT create_hypertable(
    'market_snapshots',
    'snapshot_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Add compression policies
-- Orders: compress after 14 days
SELECT add_compression_policy(
    'orders',
    INTERVAL '14 days',
    if_not_exists => TRUE
);

-- Positions: compress after 14 days
SELECT add_compression_policy(
    'positions',
    INTERVAL '14 days',
    if_not_exists => TRUE
);

-- Trades: compress after 14 days
SELECT add_compression_policy(
    'trades',
    INTERVAL '14 days',
    if_not_exists => TRUE
);

-- Market snapshots: compress after 7 days
SELECT add_compression_policy(
    'market_snapshots',
    INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Add retention policies
-- Orders: keep 365 days
SELECT add_retention_policy(
    'orders',
    INTERVAL '365 days',
    if_not_exists => TRUE
);

-- Positions: keep 365 days
SELECT add_retention_policy(
    'positions',
    INTERVAL '365 days',
    if_not_exists => TRUE
);

-- Trades: keep 365 days
SELECT add_retention_policy(
    'trades',
    INTERVAL '365 days',
    if_not_exists => TRUE
);

-- Market snapshots: keep 90 days
SELECT add_retention_policy(
    'market_snapshots',
    INTERVAL '90 days',
    if_not_exists => TRUE
);

-- Create continuous aggregates
-- Bot performance hourly
CREATE MATERIALIZED VIEW IF NOT EXISTS bot_performance_hourly
WITH (timescaledb.continuous) AS
SELECT
    o.bot_id,
    time_bucket('1 hour', t.executed_at) AS hour,
    COUNT(*) AS trades_count,
    SUM(t.executed_size * t.executed_price) AS volume_usdc,
    SUM(t.fees_paid) AS total_fees,
    SUM(t.gas_cost_usdc) AS total_gas_cost,
    AVG(t.slippage) AS avg_slippage,
    MIN(t.executed_at) AS first_trade_at,
    MAX(t.executed_at) AS last_trade_at
FROM trades t
JOIN orders o ON t.order_id = o.order_id
GROUP BY o.bot_id, hour;

-- Bot P&L daily
CREATE MATERIALIZED VIEW IF NOT EXISTS bot_pnl_daily
WITH (timescaledb.continuous) AS
SELECT
    bot_id,
    time_bucket('1 day', closed_at) AS day,
    COUNT(*) AS positions_closed,
    SUM(realized_pnl) AS total_pnl,
    AVG(realized_pnl) AS avg_pnl,
    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END)::FLOAT / COUNT(*)::FLOAT AS win_rate,
    MIN(closed_at) AS first_close_at,
    MAX(closed_at) AS last_close_at
FROM positions
WHERE closed_at IS NOT NULL
GROUP BY bot_id, day;

-- Market price 5-minute OHLC
CREATE MATERIALIZED VIEW IF NOT EXISTS market_price_5min
WITH (timescaledb.continuous) AS
SELECT
    market_id,
    time_bucket('5 minutes', snapshot_at) AS bucket,
    FIRST(yes_price, snapshot_at) AS open_yes,
    MAX(yes_price) AS high_yes,
    MIN(yes_price) AS low_yes,
    LAST(yes_price, snapshot_at) AS close_yes,
    FIRST(no_price, snapshot_at) AS open_no,
    MAX(no_price) AS high_no,
    MIN(no_price) AS low_no,
    LAST(no_price, snapshot_at) AS close_no,
    AVG(liquidity) AS avg_liquidity,
    SUM(volume) AS total_volume
FROM market_snapshots
GROUP BY market_id, bucket;

-- Add refresh policies for continuous aggregates
SELECT add_continuous_aggregate_policy(
    'bot_performance_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

SELECT add_continuous_aggregate_policy(
    'bot_pnl_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

SELECT add_continuous_aggregate_policy(
    'market_price_5min',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '5 minutes',
    if_not_exists => TRUE
);
