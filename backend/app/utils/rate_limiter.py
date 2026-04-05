"""Token bucket rate limiter for API calls."""
from fastapi import Request
import asyncio
import time
from typing import Dict, Optional
import structlog

logger = structlog.get_logger()

class TokenBucket:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket.
        
        Args:
            rate: Tokens added per second
            capacity: Maximum tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self._tokens = float(capacity)
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    @property
    def tokens(self) -> float:
        """Current token count with lazy refill based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self.last_update = now
        return self._tokens

    @tokens.setter
    def tokens(self, value: float):
        self._tokens = float(value)
    
    async def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait for tokens
            
        Returns:
            True if tokens acquired, False if timeout
        """
        async with self._lock:
            start_time = time.time()
            
            while True:
                # Add tokens based on time elapsed
                now = time.time()
                
                # Check if we have enough tokens
                if self.tokens >= tokens:
                    self.tokens = self.tokens - tokens
                    return True
                
                # Check timeout
                if timeout is not None and (now - start_time) >= timeout:
                    return False
                
                # Wait a bit before retrying
                await asyncio.sleep(0.1)
    
    async def __aenter__(self):
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class RateLimiter:
    """Rate limiter manager for multiple APIs."""
    
    def __init__(self):
        self._buckets: Dict[str, TokenBucket] = {}
    
    def create_bucket(self, name: str, requests_per_minute: int) -> TokenBucket:
        """Create a new rate limiter bucket."""
        rate = requests_per_minute / 60.0  # Convert to per second
        bucket = TokenBucket(rate=rate, capacity=requests_per_minute)
        self._buckets[name] = bucket
        logger.info(
            "Created rate limiter bucket",
            name=name,
            rpm=requests_per_minute,
            rate=rate
        )
        return bucket
    
    def get_bucket(self, name: str) -> Optional[TokenBucket]:
        """Get an existing bucket."""
        return self._buckets.get(name)
    
    async def acquire(self, name: str, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """Acquire tokens from a named bucket."""
        bucket = self._buckets.get(name)
        if not bucket:
            raise ValueError(f"No rate limiter bucket named '{name}'")
        return await bucket.acquire(tokens, timeout)


# Auth rate limiter
_AUTH_RPM = 10
_auth_buckets: dict[str, TokenBucket] = {}

def _get_auth_bucket(ip: str) -> TokenBucket:
    """Return (or lazily create) a per-IP token bucket for auth routes."""
    if ip not in _auth_buckets:
        _auth_buckets[ip] = TokenBucket(rate=_AUTH_RPM / 60.0, capacity=_AUTH_RPM)
    return _auth_buckets[ip]

async def auth_rate_limiter(request: Request) -> None:
    """
    FastAPI dependency - Inject with ''Depend (auth_rate_limiter)''.

    Allow up to 10 requests per minute per client IP.
    Returns HTTP 429 when the bucket is exhausted.
    """
    ip = request.client.host if request.client else "unknown"
    bucket = _get_auth_bucket(ip)

    acquired = await bucket.acquire(tokens=1, timeout=0) #non-blocking
    if not acquired:
        raise RateLimitExceeded(f"Too many login attempts. Please try again later.")
    
# Global rate limiter instance
rate_limiter = RateLimiter()


async def with_retry(
    func,
    max_retries: int = 3,
    base_delay: float = 1.0,
    exponential: bool = True,
    *args,
    **kwargs
):
    """
    Execute function with exponential backoff retry.
    
    Args:
        func: Async function to execute
        max_retries: Maximum number of retries
        base_delay: Base delay between retries
        exponential: Use exponential backoff
        *args, **kwargs: Arguments to pass to func
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            if attempt >= max_retries:
                logger.error(
                    "Max retries exceeded",
                    func=func.__name__,
                    retries=max_retries,
                    error=str(e)
                )
                raise
            
            delay = base_delay * (2 ** attempt if exponential else 1)
            logger.warning(
                "Retrying after error",
                func=func.__name__,
                attempt=attempt + 1,
                max_retries=max_retries,
                delay=delay,
                error=str(e)
            )
            await asyncio.sleep(delay)
    
    raise last_exception


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass
