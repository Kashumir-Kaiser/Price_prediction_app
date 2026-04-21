"""Integration tests for FastAPI endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """GET /api/health should return 200."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_list_symbols(client: AsyncClient):
    """GET /api/stocks should return a list."""
    response = await client.get("/api/stocks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_symbol_history(client: AsyncClient):
    """GET /api/stocks/BTC/USD/history should return price history."""
    response = await client.get("/api/stocks/BTC/USD/history")
    assert response.status_code == 200
    data = response.json()
    assert "prices" in data or "data" in data


@pytest.mark.asyncio
async def test_predict_unauthenticated_401(client: AsyncClient):
    """POST /api/predict without token should return 401."""
    response = await client.post("/api/predict", json={"symbol": "BTC/USD", "horizon": 1})
    assert response.status_code == 401
