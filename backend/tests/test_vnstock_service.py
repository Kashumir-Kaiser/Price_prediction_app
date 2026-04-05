"""Tests for vnstock service."""
import pytest
import pandas as pd
from unittest.mock import patch, AsyncMock
import asyncio

from app.services.vnstock_service import fetch_ohlcv, fetch_financials, validate_symbol


class TestValidateSymbol:
    """Test symbol validation."""
    
    @pytest.mark.asyncio
    async def test_valid_symbols(self):
        """Test valid VN stock symbols."""
        with patch('app.services.vnstock_service.get_all_symbols', return_value=['VNM', 'VIC', 'FPT']):
            assert await validate_symbol('VNM') is True
            assert await validate_symbol('VIC') is True
    
    @pytest.mark.asyncio
    async def test_invalid_symbols(self):
        """Test invalid symbols."""
        assert await validate_symbol('') is False
        assert await validate_symbol('INVALID123') is False
        assert await validate_symbol('A') is False


class TestFetchOHLCV:
    """Test fetch_ohlcv function."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self, mock_vnstock_data):
        """Test successful OHLCV fetch."""
        with patch('app.services.vnstock_service._fetch_ohlcv_sync', return_value=mock_vnstock_data):
            with patch('app.services.vnstock_service.validate_symbol', return_value=True):
                bars = await fetch_ohlcv('VNM', '2024-01-01', '2024-01-03')
                assert len(bars) == 3
                assert 'open' in bars[0]
                assert 'close' in bars[0]
    
    @pytest.mark.asyncio
    async def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        with patch('app.services.vnstock_service._fetch_ohlcv_sync', return_value=pd.DataFrame()):
            with patch('app.services.vnstock_service.validate_symbol', return_value=True):
                bars = await fetch_ohlcv('VNM', '2024-01-01', '2024-01-03')
                assert len(bars) == 0
    
    @pytest.mark.asyncio
    async def test_invalid_symbol_raises_error(self):
        """Test that invalid symbol raises ValueError."""
        with patch('app.services.vnstock_service.validate_symbol', return_value=False):
            with pytest.raises(ValueError, match="Invalid or unsupported symbol"):
                await fetch_ohlcv('INVALID', '2024-01-01', '2024-01-03')


class TestFetchFinancials:
    """Test fetch_financials function."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful financials fetch."""
        mock_ratios = pd.DataFrame({
            "period": ["2024Q1"],
            "P/E": [15.5],
            "P/B": [2.3]
        })
        mock_income = pd.DataFrame({
            "period": ["2024Q1"],
            "revenue": [1000000000],
            "net_profit": [100000000]
        })
        
        mock_result = {
            "ratios": mock_ratios.to_dict(orient="records"),
            "income_statement": mock_income.to_dict(orient="records"),
        }
        with patch('app.services.vnstock_service._fetch_financials_sync', return_value=mock_result):
            with patch('app.services.vnstock_service.validate_symbol', return_value=True):
                financials = await fetch_financials('VNM')
                assert 'ratios' in financials
                assert 'income_statement' in financials
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self):
        """Test connection error handling."""
        with patch('app.services.vnstock_service._fetch_financials_sync', side_effect=ConnectionError("Network error")):
            with patch('app.services.vnstock_service.validate_symbol', return_value=True):
                financials = await fetch_financials('VNM')
                # Should return empty data on connection error
                assert financials['ratios'] == []
                assert financials['income_statement'] == []


class TestThreadExecutor:
    """Test that thread executor is used for blocking calls."""
    
    @pytest.mark.asyncio
    async def test_thread_executor_usage(self, mock_vnstock_data):
        """Verify that vnstock calls use thread executor."""
        with patch('app.services.vnstock_service.validate_symbol', return_value=True):
            with patch('asyncio.get_event_loop') as mock_loop:
                mock_executor = AsyncMock(return_value=mock_vnstock_data)
                mock_loop.return_value.run_in_executor = mock_executor

                await fetch_ohlcv('VNM', '2024-01-01', '2024-01-03')

                # Verify run_in_executor was called
                assert mock_executor.called
