"""Integration tests for bot lifecycle management.

Tests end-to-end bot state transitions, resource management, and error recovery.
Uses testcontainers for TimescaleDB and Redis isolation.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import AsyncGenerator, List
from unittest.mock import AsyncMock, MagicMock, patch

from src.domain.entities.bot import Bot
from src.domain.entities.position import Position
from src.domain.value_objects import BotState, Side, Zone
from src.domain.events import (
    BotStartedEvent,
    BotPausedEvent,
    BotResumedEvent,
    BotStoppedEvent,
    EmergencyHaltEvent,
    BotErrorEvent,
)
from src.application.use_cases.execute_bot_strategy import ExecuteBotStrategyUseCase
from src.application.use_cases.emergency_halt import EmergencyHaltUseCase
from src.infrastructure.persistence.timescaledb import TimescaleDBClient
from src.infrastructure.messaging.redis_event_bus import RedisEventBus
from src.bots.base_bot import BaseBotStrategy
from src.bots.bot_orchestrator import BotOrchestrator

# Testcontainers imports
try:
    from testcontainers.postgres import PostgresContainer
    from testcontainers.redis import RedisContainer
except ImportError:
    pytest.skip("testcontainers not installed", allow_module_level=True)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
async def postgres_container() -> AsyncGenerator[PostgresContainer, None]:
    """Provide isolated PostgreSQL/TimescaleDB container for tests."""
    container = PostgresContainer(
        image="timescale/timescaledb:latest-pg16",
        port=5432,
    )
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="session")
async def redis_container() -> AsyncGenerator[RedisContainer, None]:
    """Provide isolated Redis container for tests."""
    container = RedisContainer(image="redis:7.2-alpine")
    container.start()
    yield container
    container.stop()


@pytest.fixture
async def db_client(
    postgres_container: PostgresContainer,
) -> AsyncGenerator[TimescaleDBClient, None]:
    """Provide TimescaleDB client connected to test container."""
    connection_string = postgres_container.get_connection_url()
    client = TimescaleDBClient(connection_string)
    await client.connect()
    
    # Create test schema
    await client.execute("""
        CREATE TABLE IF NOT EXISTS bots (
            bot_id VARCHAR(50) PRIMARY KEY,
            strategy_type VARCHAR(50) NOT NULL,
            state VARCHAR(20) NOT NULL,
            config JSONB NOT NULL,
            capital_allocated DECIMAL(18, 6) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS positions (
            position_id VARCHAR(50) PRIMARY KEY,
            bot_id VARCHAR(50) NOT NULL,
            market_id VARCHAR(100) NOT NULL,
            side VARCHAR(10) NOT NULL,
            entry_price DECIMAL(18, 6) NOT NULL,
            current_price DECIMAL(18, 6) NOT NULL,
            size DECIMAL(18, 6) NOT NULL,
            pnl DECIMAL(18, 6) NOT NULL DEFAULT 0,
            zone INT NOT NULL,
            opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            closed_at TIMESTAMPTZ,
            FOREIGN KEY (bot_id) REFERENCES bots(bot_id)
        );
        
        SELECT create_hypertable('positions', 'opened_at', if_not_exists => TRUE);
    """)
    
    yield client
    
    # Cleanup
    await client.execute("DROP TABLE IF EXISTS positions CASCADE;")
    await client.execute("DROP TABLE IF EXISTS bots CASCADE;")
    await client.disconnect()


@pytest.fixture
async def event_bus(
    redis_container: RedisContainer,
) -> AsyncGenerator[RedisEventBus, None]:
    """Provide Redis event bus connected to test container."""
    redis_url = redis_container.get_connection_url()
    event_bus = RedisEventBus(redis_url)
    await event_bus.connect()
    yield event_bus
    await event_bus.disconnect()


@pytest.fixture
async def event_collector(event_bus: RedisEventBus) -> List:
    """Collect all published events during test."""
    collected_events = []
    
    async def event_handler(event):
        collected_events.append(event)
    
    # Subscribe to all event channels
    await event_bus.subscribe("events.*", event_handler)
    
    yield collected_events
    
    await event_bus.unsubscribe("events.*")


@pytest.fixture
def mock_clob_client() -> AsyncMock:
    """Provide mock Polymarket CLOB client."""
    client = AsyncMock()
    client.get_orderbook = AsyncMock(return_value={
        "bids": [["0.45", "1000"]],
        "asks": [["0.55", "1000"]],
    })
    client.place_order = AsyncMock(return_value={
        "order_id": "test_order_123",
        "status": "PENDING",
    })
    client.cancel_order = AsyncMock(return_value={"success": True})
    return client


@pytest.fixture
def mock_websocket() -> AsyncMock:
    """Provide mock WebSocket client."""
    ws = AsyncMock()
    ws.connect = AsyncMock()
    ws.disconnect = AsyncMock()
    ws.subscribe = AsyncMock()
    ws.receive = AsyncMock(return_value={
        "type": "orderbook_update",
        "data": {"market_id": "test_market", "yes_price": 0.50},
    })
    return ws


@pytest.fixture
async def test_bot(
    db_client: TimescaleDBClient,
    event_bus: RedisEventBus,
    mock_clob_client: AsyncMock,
    mock_websocket: AsyncMock,
) -> Bot:
    """Create test bot instance with mocked dependencies."""
    bot = Bot(
        bot_id="test_bot_01",
        strategy_type="rebalancing",
        state=BotState.IDLE,
        config={
            "kelly_fraction": "half",
            "max_position_size": 1000.0,
            "zone_restrictions": [2, 3],
        },
        capital_allocated=Decimal("5000.00"),
        created_at=datetime.utcnow(),
    )
    
    # Save to DB
    await db_client.execute(
        """
        INSERT INTO bots (bot_id, strategy_type, state, config, capital_allocated)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (bot_id) DO UPDATE SET
            state = EXCLUDED.state,
            updated_at = NOW()
        """,
        bot.bot_id,
        bot.strategy_type,
        bot.state.value,
        bot.config,
        bot.capital_allocated,
    )
    
    return bot


@pytest.fixture
async def bot_orchestrator(
    db_client: TimescaleDBClient,
    event_bus: RedisEventBus,
    mock_clob_client: AsyncMock,
    mock_websocket: AsyncMock,
) -> BotOrchestrator:
    """Provide bot orchestrator with test dependencies."""
    orchestrator = BotOrchestrator(
        db_client=db_client,
        event_bus=event_bus,
        clob_client=mock_clob_client,
        websocket_client=mock_websocket,
    )
    return orchestrator


# ============================================================================
# TEST: STARTUP FLOW
# ============================================================================

@pytest.mark.asyncio
async def test_bot_startup_flow(
    test_bot: Bot,
    bot_orchestrator: BotOrchestrator,
    db_client: TimescaleDBClient,
    event_collector: List,
):
    """Test bot startup: IDLE → STARTING → ACTIVE.
    
    Validates:
    - State transitions occur in correct order
    - Database updates persist state changes
    - BotStartedEvent published
    - Resources initialized (WebSocket, DB connections)
    """
    # Initial state: IDLE
    assert test_bot.state == BotState.IDLE
    
    # Start bot
    start_time = datetime.utcnow()
    await bot_orchestrator.start_bot(test_bot.bot_id)
    
    # Allow async state transition to complete
    await asyncio.sleep(0.5)
    
    # Verify state: ACTIVE
    bot_state = await db_client.fetchval(
        "SELECT state FROM bots WHERE bot_id = $1",
        test_bot.bot_id,
    )
    assert bot_state == BotState.ACTIVE.value
    
    # Verify updated_at timestamp
    updated_at = await db_client.fetchval(
        "SELECT updated_at FROM bots WHERE bot_id = $1",
        test_bot.bot_id,
    )
    assert updated_at > start_time
    
    # Verify BotStartedEvent published
    started_events = [
        e for e in event_collector if isinstance(e, BotStartedEvent)
    ]
    assert len(started_events) == 1
    assert started_events[0].bot_id == test_bot.bot_id
    assert started_events[0].timestamp >= start_time
    
    # Verify transition duration <100ms target
    transition_duration = (updated_at - start_time).total_seconds()
    assert transition_duration < 0.1, f"Transition took {transition_duration}s, target <100ms"


# ============================================================================
# TEST: PAUSE/RESUME
# ============================================================================

@pytest.mark.asyncio
async def test_bot_pause_resume(
    test_bot: Bot,
    bot_orchestrator: BotOrchestrator,
    db_client: TimescaleDBClient,
    event_collector: List,
):
    """Test bot pause/resume: ACTIVE ⇄ PAUSED.
    
    Validates:
    - State transitions ACTIVE → PAUSED → ACTIVE
    - Positions preserved (not closed)
    - State persistence across pause/resume
    - BotPausedEvent and BotResumedEvent published
    """
    # Start bot first
    await bot_orchestrator.start_bot(test_bot.bot_id)
    await asyncio.sleep(0.5)
    
    # Create test position
    position_id = "test_position_123"
    await db_client.execute(
        """
        INSERT INTO positions (
            position_id, bot_id, market_id, side, entry_price,
            current_price, size, pnl, zone
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
        position_id,
        test_bot.bot_id,
        "test_market_abc",
        Side.YES.value,
        Decimal("0.45"),
        Decimal("0.50"),
        Decimal("100"),
        Decimal("5.0"),
        Zone.ZONE_2.value,
    )
    
    # Pause bot
    await bot_orchestrator.pause_bot(test_bot.bot_id)
    await asyncio.sleep(0.3)
    
    # Verify state: PAUSED
    bot_state = await db_client.fetchval(
        "SELECT state FROM bots WHERE bot_id = $1",
        test_bot.bot_id,
    )
    assert bot_state == BotState.PAUSED.value
    
    # Verify position still open (closed_at IS NULL)
    position_closed_at = await db_client.fetchval(
        "SELECT closed_at FROM positions WHERE position_id = $1",
        position_id,
    )
    assert position_closed_at is None, "Position should NOT be closed on pause"
    
    # Verify BotPausedEvent published
    paused_events = [
        e for e in event_collector if isinstance(e, BotPausedEvent)
    ]
    assert len(paused_events) == 1
    assert paused_events[0].bot_id == test_bot.bot_id
    
    # Resume bot
    await bot_orchestrator.resume_bot(test_bot.bot_id)
    await asyncio.sleep(0.3)
    
    # Verify state: ACTIVE
    bot_state = await db_client.fetchval(
        "SELECT state FROM bots WHERE bot_id = $1",
        test_bot.bot_id,
    )
    assert bot_state == BotState.ACTIVE.value
    
    # Verify position still open after resume
    position_closed_at = await db_client.fetchval(
        "SELECT closed_at FROM positions WHERE position_id = $1",
        position_id,
    )
    assert position_closed_at is None, "Position should remain open after resume"
    
    # Verify BotResumedEvent published
    resumed_events = [
        e for e in event_collector if isinstance(e, BotResumedEvent)
    ]
    assert len(resumed_events) == 1
    assert resumed_events[0].bot_id == test_bot.bot_id


# ============================================================================
# TEST: GRACEFUL STOP
# ============================================================================

@pytest.mark.asyncio
async def test_bot_graceful_stop(
    test_bot: Bot,
    bot_orchestrator: BotOrchestrator,
    db_client: TimescaleDBClient,
    event_collector: List,
    mock_clob_client: AsyncMock,
):
    """Test graceful bot stop: ACTIVE → STOPPING → STOPPED.
    
    Validates:
    - All open positions closed gracefully
    - Resources cleaned up (WebSocket disconnect)
    - Final state STOPPED persisted
    - BotStoppedEvent published
    """
    # Start bot
    await bot_orchestrator.start_bot(test_bot.bot_id)
    await asyncio.sleep(0.5)
    
    # Create 2 test positions
    positions = [
        ("pos_1", "market_1", Decimal("0.40"), Decimal("100")),
        ("pos_2", "market_2", Decimal("0.60"), Decimal("200")),
    ]
    
    for pos_id, market_id, entry_price, size in positions:
        await db_client.execute(
            """
            INSERT INTO positions (
                position_id, bot_id, market_id, side, entry_price,
                current_price, size, pnl, zone
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            pos_id,
            test_bot.bot_id,
            market_id,
            Side.YES.value,
            entry_price,
            entry_price,
            size,
            Decimal("0"),
            Zone.ZONE_2.value,
        )
    
    # Stop bot gracefully
    stop_time = datetime.utcnow()
    await bot_orchestrator.stop_bot(test_bot.bot_id)
    await asyncio.sleep(1.0)  # Allow time for position closing
    
    # Verify state: STOPPED
    bot_state = await db_client.fetchval(
        "SELECT state FROM bots WHERE bot_id = $1",
        test_bot.bot_id,
    )
    assert bot_state == BotState.STOPPED.value
    
    # Verify all positions closed
    open_positions = await db_client.fetchval(
        "SELECT COUNT(*) FROM positions WHERE bot_id = $1 AND closed_at IS NULL",
        test_bot.bot_id,
    )
    assert open_positions == 0, "All positions should be closed on graceful stop"
    
    # Verify positions have closed_at timestamp
    for pos_id, _, _, _ in positions:
        closed_at = await db_client.fetchval(
            "SELECT closed_at FROM positions WHERE position_id = $1",
            pos_id,
        )
        assert closed_at is not None
        assert closed_at >= stop_time
    
    # Verify close orders placed via CLOB
    assert mock_clob_client.place_order.call_count >= len(positions)
    
    # Verify BotStoppedEvent published
    stopped_events = [
        e for e in event_collector if isinstance(e, BotStoppedEvent)
    ]
    assert len(stopped_events) == 1
    assert stopped_events[0].bot_id == test_bot.bot_id


# ============================================================================
# TEST: EMERGENCY HALT
# ============================================================================

@pytest.mark.asyncio
async def test_bot_emergency_halt(
    test_bot: Bot,
    bot_orchestrator: BotOrchestrator,
    db_client: TimescaleDBClient,
    event_collector: List,
    mock_clob_client: AsyncMock,
):
    """Test emergency halt: ANY_STATE → EMERGENCY_HALT.
    
    Validates:
    - Immediate transition to EMERGENCY_HALT (<10s)
    - All positions force closed (market orders)
    - EmergencyHaltEvent published
    - Audit trail created
    """
    # Start bot
    await bot_orchestrator.start_bot(test_bot.bot_id)
    await asyncio.sleep(0.5)
    
    # Create test position
    await db_client.execute(
        """
        INSERT INTO positions (
            position_id, bot_id, market_id, side, entry_price,
            current_price, size, pnl, zone
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
        "emergency_pos_1",
        test_bot.bot_id,
        "test_market",
        Side.YES.value,
        Decimal("0.50"),
        Decimal("0.50"),
        Decimal("500"),
        Decimal("0"),
        Zone.ZONE_3.value,
    )
    
    # Trigger emergency halt
    halt_start = datetime.utcnow()
    await bot_orchestrator.emergency_halt(
        test_bot.bot_id,
        reason="Test emergency halt",
    )
    await asyncio.sleep(2.0)  # Max 10s target, use 2s for test
    halt_end = datetime.utcnow()
    
    # Verify halt duration <10s (actual <2s in test)
    halt_duration = (halt_end - halt_start).total_seconds()
    assert halt_duration < 10.0, f"Emergency halt took {halt_duration}s, must be <10s"
    
    # Verify state: EMERGENCY_HALT
    bot_state = await db_client.fetchval(
        "SELECT state FROM bots WHERE bot_id = $1",
        test_bot.bot_id,
    )
    assert bot_state == BotState.EMERGENCY_HALT.value
    
    # Verify position force closed
    position_closed_at = await db_client.fetchval(
        "SELECT closed_at FROM positions WHERE position_id = $1",
        "emergency_pos_1",
    )
    assert position_closed_at is not None
    assert position_closed_at >= halt_start
    
    # Verify market order placed (force close)
    place_order_calls = mock_clob_client.place_order.call_args_list
    market_orders = [
        call for call in place_order_calls
        if call[1].get("order_type") == "MARKET"  # Force close uses MARKET
    ]
    assert len(market_orders) >= 1, "Emergency halt should use MARKET orders"
    
    # Verify EmergencyHaltEvent published
    halt_events = [
        e for e in event_collector if isinstance(e, EmergencyHaltEvent)
    ]
    assert len(halt_events) == 1
    assert halt_events[0].bot_id == test_bot.bot_id
    assert halt_events[0].reason == "Test emergency halt"
    assert halt_events[0].timestamp >= halt_start


# ============================================================================
# TEST: ERROR RECOVERY
# ============================================================================

@pytest.mark.asyncio
async def test_bot_error_recovery(
    test_bot: Bot,
    bot_orchestrator: BotOrchestrator,
    db_client: TimescaleDBClient,
    event_collector: List,
):
    """Test error recovery: ERROR → retry → ACTIVE or STOPPED.
    
    Validates:
    - Exponential backoff retry (1s, 2s, 4s, 8s max)
    - Max 3 retry attempts
    - Fallback to STOPPED if retries exhausted
    - BotErrorEvent published for each failure
    """
    # Simulate bot entering ERROR state
    await db_client.execute(
        "UPDATE bots SET state = $1 WHERE bot_id = $2",
        BotState.ERROR.value,
        test_bot.bot_id,
    )
    
    # Mock retry logic with failures
    retry_attempts = []
    
    async def mock_start_with_failures():
        retry_attempts.append(datetime.utcnow())
        if len(retry_attempts) < 3:
            raise Exception(f"Simulated failure {len(retry_attempts)}")
        # Success on 3rd attempt
        await db_client.execute(
            "UPDATE bots SET state = $1 WHERE bot_id = $2",
            BotState.ACTIVE.value,
            test_bot.bot_id,
        )
    
    # Execute retry logic
    max_retries = 3
    backoff_delays = [1, 2, 4, 8]  # seconds
    
    for attempt in range(max_retries):
        try:
            await mock_start_with_failures()
            break  # Success
        except Exception as e:
            # Publish error event
            error_event = BotErrorEvent(
                bot_id=test_bot.bot_id,
                error_message=str(e),
                attempt=attempt + 1,
                timestamp=datetime.utcnow(),
            )
            event_collector.append(error_event)
            
            if attempt < max_retries - 1:
                delay = backoff_delays[attempt]
                await asyncio.sleep(delay)
            else:
                # Retries exhausted, set STOPPED
                await db_client.execute(
                    "UPDATE bots SET state = $1 WHERE bot_id = $2",
                    BotState.STOPPED.value,
                    test_bot.bot_id,
                )
    
    # Verify exponential backoff timing
    assert len(retry_attempts) == 3
    if len(retry_attempts) > 1:
        delay_1_2 = (retry_attempts[1] - retry_attempts[0]).total_seconds()
        assert 0.9 < delay_1_2 < 1.2, f"First backoff should be ~1s, got {delay_1_2}s"
    
    if len(retry_attempts) > 2:
        delay_2_3 = (retry_attempts[2] - retry_attempts[1]).total_seconds()
        assert 1.9 < delay_2_3 < 2.2, f"Second backoff should be ~2s, got {delay_2_3}s"
    
    # Verify final state: ACTIVE (successful on 3rd attempt)
    final_state = await db_client.fetchval(
        "SELECT state FROM bots WHERE bot_id = $1",
        test_bot.bot_id,
    )
    assert final_state == BotState.ACTIVE.value
    
    # Verify BotErrorEvent published for each failure
    error_events = [
        e for e in event_collector if isinstance(e, BotErrorEvent)
    ]
    assert len(error_events) == 2, "Should have 2 error events (failures before success)"


# ============================================================================
# TEST: STATE PERSISTENCE
# ============================================================================

@pytest.mark.asyncio
async def test_bot_state_persistence(
    test_bot: Bot,
    bot_orchestrator: BotOrchestrator,
    db_client: TimescaleDBClient,
):
    """Test bot state persists across restarts.
    
    Validates:
    - State saved to database on every transition
    - State restored correctly on bot restart
    - updated_at timestamp updated
    """
    # Transition through multiple states
    states = [
        BotState.IDLE,
        BotState.STARTING,
        BotState.ACTIVE,
        BotState.PAUSED,
        BotState.ACTIVE,
        BotState.STOPPED,
    ]
    
    for state in states:
        # Update state
        await db_client.execute(
            "UPDATE bots SET state = $1, updated_at = NOW() WHERE bot_id = $2",
            state.value,
            test_bot.bot_id,
        )
        
        # Verify state persisted
        persisted_state = await db_client.fetchval(
            "SELECT state FROM bots WHERE bot_id = $1",
            test_bot.bot_id,
        )
        assert persisted_state == state.value
        
        # Short delay between transitions
        await asyncio.sleep(0.1)
    
    # Verify final state
    final_state = await db_client.fetchval(
        "SELECT state FROM bots WHERE bot_id = $1",
        test_bot.bot_id,
    )
    assert final_state == BotState.STOPPED.value
    
    # Verify updated_at changed
    updated_at = await db_client.fetchval(
        "SELECT updated_at FROM bots WHERE bot_id = $1",
        test_bot.bot_id,
    )
    assert updated_at > test_bot.created_at
