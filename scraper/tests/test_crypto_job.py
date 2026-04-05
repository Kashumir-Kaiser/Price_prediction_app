"""Tests for crypto scraper job."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import types
import sys

from scraper.jobs.crypto_job import run_crypto_job


class TestCryptoJob:
    """Test crypto job functionality."""
    
    @pytest.mark.asyncio
    async def test_job_iterates_all_symbols(self):
        """Test that job iterates over all crypto symbols."""
        mock_bars = [
            {"t": "2024-01-01T00:00:00Z", "o": 1, "h": 2, "l": 0, "c": 1.5, "v": 100, "vw": 1.5}
        ]
        
        with patch('scraper.jobs.crypto_job.fetch_bars', return_value=mock_bars):
            with patch('scraper.jobs.crypto_job.AsyncSessionLocal') as mock_session:
                mock_db = AsyncMock()
                mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
                mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
                
                with patch('scraper.jobs.crypto_job.crud.upsert_crypto_bar') as mock_upsert:
                    with patch('scraper.jobs.crypto_job.CRYPTO_SYMBOLS', ['BTC/USD', 'ETH/USD']):
                        await run_crypto_job()
                        
                        # Should call fetch_bars for each symbol
                        assert mock_upsert.call_count == 2
    
    @pytest.mark.asyncio
    async def test_job_publishes_redis_event(self):
        """Test that job publishes Redis event on completion."""
        mock_bars = []
        mock_r = AsyncMock()
        mock_redis_asyncio = types.ModuleType("redis.asyncio")
        mock_redis_asyncio.from_url = MagicMock(return_value=mock_r)
        mock_redis = types.ModuleType("redis")
        mock_redis.asyncio = mock_redis_asyncio
        
        with patch('scraper.jobs.crypto_job.fetch_bars', return_value=mock_bars):
            with patch('scraper.jobs.crypto_job.AsyncSessionLocal'):
                with patch.dict(sys.modules, {"redis": mock_redis, "redis.asyncio": mock_redis_asyncio}):
                    with patch('scraper.jobs.crypto_job.CRYPTO_SYMBOLS', ['BTC/USD']):
                        await run_crypto_job()
                        
                        # Should publish event
                        mock_r.publish.assert_called_with("market_updates", "crypto_updated")
    
    @pytest.mark.asyncio
    async def test_job_handles_errors_gracefully(self):
        """Test that job continues despite individual symbol errors."""
        with patch('scraper.jobs.crypto_job.fetch_bars', side_effect=Exception("API error")):
            with patch('scraper.jobs.crypto_job.AsyncSessionLocal'):
                with patch('scraper.jobs.crypto_job.CRYPTO_SYMBOLS', ['BTC/USD', 'ETH/USD']):
                    # Should not raise exception
                    await run_crypto_job()
