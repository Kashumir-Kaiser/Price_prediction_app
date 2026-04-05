"""Tests for VN stock scraper job."""
import pytest
from unittest.mock import patch, AsyncMock
from datetime import date

from scraper.jobs.vn_stock_job import run_vn_stock_job, DEFAULT_VN_SYMBOLS


class TestVNStockJob:
    """Test VN stock job functionality."""
    
    @pytest.mark.asyncio
    async def test_job_sleeps_between_tickers(self):
        """Test that job sleeps between ticker fetches."""
        mock_bars = [{"ts": date.today(), "open": 100, "high": 105, "low": 98, "close": 102, "volume": 1000000}]
        mock_financials = {"ratios": [], "income_statement": []}
        
        with patch("scraper.jobs.vn_stock_job.fetch_ohlcv", return_value=mock_bars), \
             patch("scraper.jobs.vn_stock_job.fetch_financials", return_value=mock_financials), \
             patch("scraper.jobs.vn_stock_job.AsyncSessionLocal"), \
             patch("scraper.jobs.vn_stock_job.crud.get_watchlist", new_callable=AsyncMock, return_value=[]), \
             patch("scraper.jobs.vn_stock_job.crud.add_to_watchlist", new_callable=AsyncMock), \
             patch("scraper.jobs.vn_stock_job.crud.upsert_stock_bar", new_callable=AsyncMock), \
             patch("scraper.jobs.vn_stock_job.sleep_between_tickers", new_callable=AsyncMock) as mock_sleep, \
             patch("scraper.jobs.vn_stock_job.DEFAULT_VN_SYMBOLS", ["VNM", "VIC"]):
            await run_vn_stock_job()

            # Should sleep between tickers
            assert mock_sleep.call_count == 2
    
    @pytest.mark.asyncio
    async def test_job_handles_empty_dataframe(self):
        """Test that empty DataFrame doesn't cause issues."""
        with patch("scraper.jobs.vn_stock_job.fetch_ohlcv", return_value=[]), \
             patch("scraper.jobs.vn_stock_job.fetch_financials", return_value={"ratios": [], "income_statement": []}), \
             patch("scraper.jobs.vn_stock_job.AsyncSessionLocal"), \
             patch("scraper.jobs.vn_stock_job.crud.get_watchlist", new_callable=AsyncMock, return_value=[]), \
             patch("scraper.jobs.vn_stock_job.crud.add_to_watchlist", new_callable=AsyncMock), \
             patch("scraper.jobs.vn_stock_job.DEFAULT_VN_SYMBOLS", ["VNM"]):
            # Should not raise exception
            await run_vn_stock_job()
    
    @pytest.mark.asyncio
    async def test_job_catches_db_errors(self):
        """Test that DB commit errors bubble up."""
        mock_bars = [{"ts": date.today(), "open": 100, "high": 105, "low": 98, "close": 102, "volume": 1000000}]
        
        with patch("scraper.jobs.vn_stock_job.fetch_ohlcv", return_value=mock_bars):
            with patch("scraper.jobs.vn_stock_job.AsyncSessionLocal") as mock_session:
                mock_db = AsyncMock()
                mock_db.commit.side_effect = Exception("DB error")
                mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
                mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
                
                with patch("scraper.jobs.vn_stock_job.crud.get_watchlist", new_callable=AsyncMock, return_value=[]), \
                     patch("scraper.jobs.vn_stock_job.crud.add_to_watchlist", new_callable=AsyncMock), \
                     patch("scraper.jobs.vn_stock_job.crud.upsert_stock_bar", new_callable=AsyncMock), \
                     patch("scraper.jobs.vn_stock_job.fetch_financials", return_value={"ratios": [], "income_statement": []}), \
                     patch("scraper.jobs.vn_stock_job.sleep_between_tickers", new_callable=AsyncMock), \
                     patch("scraper.jobs.vn_stock_job.DEFAULT_VN_SYMBOLS", ["VNM"]):
                    with pytest.raises(Exception, match="DB error"):
                        await run_vn_stock_job()
