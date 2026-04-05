"""Alpaca Markets REST API service."""
import httpx, os, structlog
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.config import get_settings
settings = get_settings()

from app.utils.rate_limiter import rate_limiter, with_retry

logger = structlog.get_logger()

# Constants
ALPACA_KEY = settings.alpaca_api_key
ALPACA_SECRET = settings.alpaca_secret_key
BASE_URL = "https://data.alpaca.markets/v1beta3/crypto/us"

CRYPTO_SYMBOLS = ["BTC/USD", "ETH/USD", "SOL/USD"]
STABLE_SYMBOLS = ["USDT/USD", "USDC/USD"]
ALL_SYMBOLS = CRYPTO_SYMBOLS + STABLE_SYMBOLS

# Initialize rate limiter
alpaca_bucket = rate_limiter.create_bucket("alpaca", settings.alpaca_rate_limit_rpm)


def validate_symbol(symbol: str) -> bool:
    """Validate if symbol is supported."""
    return symbol in ALL_SYMBOLS


async def fetch_bars(
    symbol: str,
    timeframe: str = "1Day",
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Fetch OHLCV bars with pagination.
    
    Args:
        symbol: Trading pair symbol (e.g., "BTC/USD")
        timeframe: Bar timeframe (1Min, 15Min, 1Hour, 1Day)
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        limit: Maximum bars per request
        
    Returns:
        List of bar dictionaries
    """
    if not validate_symbol(symbol):
        raise ValueError(f"Invalid symbol: {symbol}. Supported: {ALL_SYMBOLS}")
    
    if not start:
        start = (datetime.utcnow() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    params = {
        "symbols": symbol,
        "timeframe": timeframe,
        "start": start,
        "limit": limit
    }
    if end:
        params["end"] = end
    
    headers = {
        "APCA-API-KEY-ID": ALPACA_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET
    }
    
    bars = []
    
    async def fetch_page(page_params: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch a single page with rate limiting."""
        await rate_limiter.acquire("alpaca")
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{BASE_URL}/bars",
                params=page_params,
                headers=headers
            )
            resp.raise_for_status()
            return resp.json()
    
    try:
        while True:
            data = await with_retry(fetch_page, max_retries=3, base_delay=1.0, page_params=params)
            
            # Extract bars for the symbol
            symbol_bars = data.get("bars", {}).get(symbol, [])
            bars.extend(symbol_bars)
            
            # Check for pagination
            token = data.get("next_page_token")
            if not token:
                break
            
            params["page_token"] = token
            logger.debug(
                "Paginating Alpaca bars",
                symbol=symbol,
                page_token=token,
                bars_collected=len(bars)
            )
        
        logger.info(
            "Fetched bars from Alpaca",
            symbol=symbol,
            timeframe=timeframe,
            bars_count=len(bars)
        )
        
        return bars
        
    except httpx.HTTPStatusError as e:
        logger.error(
            "Alpaca API error",
            symbol=symbol,
            status_code=e.response.status_code,
            response=e.response.text
        )
        raise
    except Exception as e:
        logger.error(
            "Error fetching bars from Alpaca",
            symbol=symbol,
            error=str(e)
        )
        raise


async def fetch_latest_bars(symbols: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
    """
    Fetch latest bars for multiple symbols.
    
    Args:
        symbols: List of symbols to fetch (defaults to ALL_SYMBOLS)
        
    Returns:
        Dictionary mapping symbol to latest bar
    """
    if symbols is None:
        symbols = ALL_SYMBOLS
    
    # Fetch last 1 day of data for each symbol
    end = datetime.utcnow()
    start = end - timedelta(days=1)
    
    result = {}
    
    for symbol in symbols:
        try:
            bars = await fetch_bars(
                symbol=symbol,
                timeframe="1Day",
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                limit=1
            )
            if bars:
                result[symbol] = bars[-1]
        except Exception as e:
            logger.error(
                "Failed to fetch latest bar",
                symbol=symbol,
                error=str(e)
            )
    
    return result


def check_stablecoin_deviation(bar: Dict[str, Any], threshold: float = 0.005) -> bool:
    """
    Check if stablecoin price deviates significantly from $1.00.
    
    Args:
        bar: Bar data with close price
        threshold: Deviation threshold (default 0.5%)
        
    Returns:
        True if deviation exceeds threshold
    """
    close = float(bar.get("c", bar.get("close", 0)))
    deviation = abs(close - 1.0)
    return deviation > threshold
