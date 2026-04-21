"""Contract tests — Pact consumer (frontend-facing)."""
import pytest
import json
from pathlib import Path

import httpx
from pact import Consumer, Provider

PACT_DIR = Path(__file__).parent / "pacts"
PACT_DIR.mkdir(parents=True, exist_ok=True)

# ──  Consumer test  ───────────────────────────────────────────────────────────

@pytest.fixture
def pact():
    return Consumer("frontend").has_pact_with(
        Provider("backend"),
        pact_dir=str(PACT_DIR),
    )


def test_get_symbols_contract(pact):
    """Contract: GET /api/stocks returns list of symbols."""
    expected = [
        {"symbol": "BTC/USD", "name": "Bitcoin / US Dollar"},
        {"symbol": "ETH/USD", "name": "Ethereum / US Dollar"},
    ]

    (pact
     .given("symbols exist")
     .upon_receiving("a request for all symbols")
     .with_request("GET", "/api/stocks")
     .will_respond_with(200, body=expected))

    with pact:
        result = httpx.get(pact.uri + "/api/stocks")
        assert result.status_code == 200
        assert result.json() == expected


def test_get_history_contract(pact):
    """Contract: GET /api/stocks/{symbol}/history returns price history."""
    expected = {
        "symbol": "BTC/USD",
        "data": [
            {"ts": "2024-01-01", "open": 42000, "high": 43000, "low": 41000, "close": 42500, "volume": 1000000},
            {"ts": "2024-01-02", "open": 42500, "high": 44000, "low": 42000, "close": 43500, "volume": 1200000},
        ]
    }

    (pact
     .given("history exists for BTC/USD")
     .upon_receiving("a request for BTC/USD history")
     .with_request("GET", "/api/stocks/BTC/USD/history")
     .will_respond_with(200, body=expected))

    with pact:
        result = httpx.get(pact.uri + "/api/stocks/BTC/USD/history")
        assert result.status_code == 200


def test_predict_contract(pact):
    """Contract: POST /api/predict with valid token returns prediction."""
    expected = {
        "symbol": "BTC/USD",
        "horizon": 1,
        "predicted_price": 45000.0,
        "confidence": 0.78,
    }

    (pact
     .given("user is authenticated")
     .upon_receiving("a prediction request")
     .with_request("POST", "/api/predict", body={"symbol": "BTC/USD", "horizon": 1}, headers={"Authorization": "Bearer token123"})
     .will_respond_with(200, body=expected))

    with pact:
        result = httpx.post(
            pact.uri + "/api/predict",
            json={"symbol": "BTC/USD", "horizon": 1},
            headers={"Authorization": "Bearer token123"},
        )
        assert result.status_code == 200
