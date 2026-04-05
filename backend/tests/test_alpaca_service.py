"""Tests for Alpaca service."""
import pytest
import httpx
from unittest.mock import Mock, patch, AsyncMock
import respx

from app.services.alpaca_service import fetch_bars, validate_symbol, CRYPTO_SYMBOLS, STABLE_SYMBOLS


class TestValidateSymbol:
    """Test symbol validation."""
    
    def test_valid_crypto_symbols(self):
        """Test that valid crypto symbols are accepted."""
        for symbol in CRYPTO_SYMBOLS:
            assert validate_symbol(symbol) is True
    
    def test_valid_stable_symbols(self):
        """Test that valid stablecoin symbols are accepted."""
        for symbol in STABLE_SYMBOLS:
            assert validate_symbol(symbol) is True
    
    def test_invalid_symbol(self):
        """Test that invalid symbols are rejected."""
        assert validate_symbol("INVALID/USD") is False
        assert validate_symbol("") is False


class TestFetchBars:
    """Test fetch_bars function."""
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_successful_fetch(self, mock_alpaca_response):
        """Test successful bar fetch."""
        # Mock the API endpoint
        route = respx.get("https://data.alpaca.markets/v1beta3/crypto/us/bars").mock(
            return_value=httpx.Response(200, json=mock_alpaca_response)
        )
        
        bars = await fetch_bars("BTC/USD", start="2024-01-01")
        
        assert len(bars) == 2
        assert bars[0]["c"] == 42500.0
        assert route.called
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_pagination(self):
        """Test pagination with next_page_token."""
        # First page response
        page1 = {
            "bars": {"BTC/USD": [{"t": "2024-01-01", "o": 1, "h": 2, "l": 0, "c": 1.5, "v": 100}]},
            "next_page_token": "token123"
        }
        # Second page response
        page2 = {
            "bars": {"BTC/USD": [{"t": "2024-01-02", "o": 1.5, "h": 2.5, "l": 1, "c": 2, "v": 200}]},
            "next_page_token": None
        }
        
        route = respx.get("https://data.alpaca.markets/v1beta3/crypto/us/bars")
        route.side_effect = [
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2)
        ]
        
        bars = await fetch_bars("BTC/USD")
        
        assert len(bars) == 2
        assert route.call_count == 2
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_invalid_symbol_raises_error(self):
        """Test that invalid symbol raises ValueError."""
        with pytest.raises(ValueError, match="Invalid symbol"):
            await fetch_bars("INVALID/USD")
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self):
        """Test rate limit triggers retry."""
        route = respx.get("https://data.alpaca.markets/v1beta3/crypto/us/bars")
        route.side_effect = [
            httpx.Response(429, json={"message": "Rate limit exceeded"}),
            httpx.Response(200, json={"bars": {"BTC/USD": []}, "next_page_token": None})
        ]
        
        bars = await fetch_bars("BTC/USD")
        
        assert route.call_count == 2
