"""Tests for rate limiter."""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock

from app.utils.rate_limiter import TokenBucket, RateLimiter, RateLimitExceeded, with_retry


class TestTokenBucket:
    """Test TokenBucket implementation."""
    
    @pytest.mark.asyncio
    async def test_acquire_success(self):
        """Test successful token acquisition."""
        bucket = TokenBucket(rate=10, capacity=10)
        
        result = await bucket.acquire()
        
        assert result is True
        assert bucket.tokens == pytest.approx(9, rel=0, abs=0.05)
    
    @pytest.mark.asyncio
    async def test_acquire_multiple_tokens(self):
        """Test acquiring multiple tokens."""
        bucket = TokenBucket(rate=10, capacity=10)
        
        result = await bucket.acquire(tokens=5)
        
        assert result is True
        assert bucket.tokens == pytest.approx(5, rel=0, abs=0.05)
    
    @pytest.mark.asyncio
    async def test_acquire_timeout(self):
        """Test acquire with timeout."""
        bucket = TokenBucket(rate=1, capacity=1)
        await bucket.acquire()  # Use the only token
        
        result = await bucket.acquire(timeout=0.1)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_token_refill(self):
        """Test tokens are refilled over time."""
        bucket = TokenBucket(rate=10, capacity=10)
        await bucket.acquire()  # Use one token
        
        initial_tokens = bucket.tokens
        await asyncio.sleep(0.2)  # Wait for refill
        
        assert bucket.tokens > initial_tokens
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using bucket as context manager."""
        bucket = TokenBucket(rate=10, capacity=10)
        
        async with bucket:
            assert bucket.tokens == pytest.approx(9, rel=0, abs=0.05)


class TestRateLimiter:
    """Test RateLimiter manager."""
    
    def test_create_bucket(self):
        """Test creating a new bucket."""
        limiter = RateLimiter()
        
        bucket = limiter.create_bucket("test", 100)
        
        assert bucket is not None
        assert "test" in limiter._buckets
    
    @pytest.mark.asyncio
    async def test_acquire_from_bucket(self):
        """Test acquiring from named bucket."""
        limiter = RateLimiter()
        limiter.create_bucket("test", 10)
        
        result = await limiter.acquire("test")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_acquire_unknown_bucket(self):
        """Test acquiring from unknown bucket raises error."""
        limiter = RateLimiter()
        
        with pytest.raises(ValueError, match="No rate limiter bucket"):
            await limiter.acquire("unknown")


class TestWithRetry:
    """Test retry decorator."""
    
    @pytest.mark.asyncio
    async def test_successful_call(self):
        """Test function succeeds on first call."""
        mock_func = AsyncMock(return_value="success")
        
        result = await with_retry(mock_func, max_retries=3)
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test function is retried on failure."""
        mock_func = AsyncMock(side_effect=[Exception("error"), "success"])
        
        result = await with_retry(mock_func, max_retries=3, base_delay=0.01)
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test exception is raised when max retries exceeded."""
        mock_func = AsyncMock(side_effect=Exception("persistent error"))
        
        with pytest.raises(Exception, match="persistent error"):
            await with_retry(mock_func, max_retries=2, base_delay=0.01)
        
        assert mock_func.call_count == 3  # Initial + 2 retries
    
    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff delays."""
        mock_func = AsyncMock(side_effect=[Exception("error"), "success"])
        
        with patch('asyncio.sleep') as mock_sleep:
            await with_retry(mock_func, max_retries=3, base_delay=1.0, exponential=True)
            
            # First retry should wait 1s, second would wait 2s
            mock_sleep.assert_called_once()
            assert mock_sleep.call_args[0][0] == 1.0
