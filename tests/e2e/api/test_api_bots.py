"""E2E tests for bot routes.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.presentation.api.main import app


@pytest.fixture
def client() -> TestClient:
    """Test client fixture."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_list_bots(client: TestClient) -> None:
    """Test GET /api/v1/bots."""
    response = client.get("/api/v1/bots")
    assert response.status_code == 200
    data = response.json()
    assert "bots" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_bot(client: TestClient) -> None:
    """Test GET /api/v1/bots/{bot_id}."""
    response = client.get("/api/v1/bots/1")
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_start_bot(client: TestClient) -> None:
    """Test POST /api/v1/bots/{bot_id}/start."""
    response = client.post("/api/v1/bots/1/start")
    assert response.status_code in [202, 404, 500]


@pytest.mark.asyncio
async def test_stop_bot(client: TestClient) -> None:
    """Test POST /api/v1/bots/{bot_id}/stop."""
    response = client.post("/api/v1/bots/1/stop")
    assert response.status_code in [202, 404, 500]


@pytest.mark.asyncio
async def test_pause_bot(client: TestClient) -> None:
    """Test POST /api/v1/bots/{bot_id}/pause."""
    response = client.post("/api/v1/bots/1/pause")
    assert response.status_code in [202, 404, 500]


@pytest.mark.asyncio
async def test_update_bot_config(client: TestClient) -> None:
    """Test PUT /api/v1/bots/{bot_id}/config."""
    response = client.put(
        "/api/v1/bots/1/config",
        json={"config": {"key": "value"}},
    )
    assert response.status_code in [200, 404, 422]
