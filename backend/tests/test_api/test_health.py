import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    """Verify that root landing endpoint responds with 200 OK and valid metadata."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert data["health"] == "/api/v1/health/live"


@pytest.mark.asyncio
async def test_liveness_probe(async_client: AsyncClient):
    """Verify that the liveness probe responds with alive status."""
    response = await async_client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
