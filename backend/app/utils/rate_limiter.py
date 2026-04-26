"""Token bucket rate limiter for API calls."""
from fastapi import Request, HTTPException, status
import asyncio
import time
from typing import Dict, Optional
import structlog

logger = structlog.get_logger()


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


class TokenBucket:
    """Async token-bucket rate limiter.

    capacity: max tokens (burst ceiling)
    rate: tokens refilled per second
    """

    def __init__(self, capacity: int, rate: float):
        self._capacity = capacity
        self._tokens = float(capacity)
        self._rate = rate
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(
            self._capacity,
            self._tokens + elapsed * self._rate
        )
        self._last_refill = now

    async def acquire(self, timeout: float = 0.0) -> bool:
        """
        Try to consume one token.

        timeout=0 -> non-blocking (return False immediately if empty)
        timeout>0 -> block up to `timeout` seconds waiting for a token

        Returns True if token acquired.
        Raises RateLimitExceeded when timeout is exceeded.
        """
        if timeout < 0:
            raise ValueError("timeout must be >= 0")

        deadline = time.monotonic() + timeout if timeout > 0 else None
        while True:
            async with self._lock:
                await self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return True
            # timeout=0 behaves as non-blocking try-acquire.
            if deadline is None:
                raise RateLimitExceeded()
            if time.monotonic() >= deadline:
                raise RateLimitExceeded()
            await asyncio.sleep(0.05)


from collections import defaultdict
_ip_buckets: dict[str, TokenBucket] = {}

async def auth_rate_limiter(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    bucket = _ip_buckets.setdefault(ip, TokenBucket(capacity=10, rate=10/60))
    try:
        await bucket.acquire(timeout=0.0)
    except RateLimitExceeded:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": "60"},
        )


class RateLimiter:
    """Rate limiter manager for multiple APIs."""

    def __init__(self):
        self._buckets: Dict[str, TokenBucket] = {}

    def create_bucket(self, name: str, requests_per_minute: int) -> TokenBucket:
        """Create a new rate limiter bucket."""
        rate = requests_per_minute / 60.0  # Convert to per second
        bucket = TokenBucket(capacity=requests_per_minute, rate=rate)
        self._buckets[name] = bucket
        logger.info(
            "Created rate limiter bucket",
            name=name,
            rpm=requests_per_minute,
            rate=rate,
        )
        return bucket

    def get_bucket(self, name: str) -> Optional[TokenBucket]:
        """Get an existing bucket."""
        return self._buckets.get(name)

    async def acquire(self, name: str, timeout: float = 0.0) -> bool:
        """Acquire a token from a named bucket."""
        bucket = self._buckets.get(name)
        if not bucket:
            raise ValueError(f"No rate limiter bucket named '{name}'")
        return await bucket.acquire(timeout=timeout)


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
                    error=str(e),
                )
                raise

            delay = base_delay * (2 ** attempt if exponential else 1)
            logger.warning(
                "Retrying after error",
                func=func.__name__,
                attempt=attempt + 1,
                max_retries=max_retries,
                delay=delay,
                error=str(e),
            )
            await asyncio.sleep(delay)

    raise last_exception
