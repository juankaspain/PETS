"""E2E tests for health routes.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import pytest
from fastapi.testclient import TestClient

from src.presentation.api.main import app


@pytest.fixture
def client() -> TestClient:
    """Test client fixture."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_liveness(client: TestClient) -> None:
    """Test GET /api/v1/health/live."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_readiness(client: TestClient) -> None:
    """Test GET /api/v1/health/ready."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data
    assert "websocket" in data


@pytest.mark.asyncio
async def test_startup(client: TestClient) -> None:
    """Test GET /api/v1/health/startup."""
    response = client.get("/api/v1/health/startup")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "migrations_applied" in data
    assert "bots_initialized" in data
