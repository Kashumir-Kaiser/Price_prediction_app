"""Vietnamese stock data service using vnstock3."""
import asyncio
from functools import partial
from typing import List, Dict, Any, Optional
import pandas as pd
import structlog

from app.config import get_settings
settings = get_settings()

from app.utils.rate_limiter import rate_limiter

logger = structlog.get_logger()

# Initialize rate limiter (30 requests per minute for vnstock)
vnstock_bucket = rate_limiter.create_bucket("vnstock", 30)

# Cache for valid symbols
_symbol_cache: Dict[str, List[str]] = {}


def _fetch_ohlcv_sync(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Synchronous OHLCV fetch using vnstock3."""
    try:
        from vnstock3 import Vnstock
        stock = Vnstock().stock(symbol=symbol, source="TCBS")
        df = stock.quote.history(start=start, end=end, interval="1D")
        return df
    except Exception as e:
        logger.error(
            "vnstock OHLCV fetch failed",
            symbol=symbol,
            error=str(e)
        )
        raise


async def fetch_ohlcv(symbol: str, start: str, end: str) -> List[Dict[str, Any]]:
    """
    Fetch OHLCV data for a Vietnamese stock asynchronously.
    
    Args:
        symbol: Stock ticker (e.g., "VNM", "VIC", "FPT")
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        
    Returns:
        List of OHLCV dictionaries
    """
    # Validate symbol
    if not await validate_symbol(symbol):
        raise ValueError(f"Invalid or unsupported symbol: {symbol}")
    
    # Acquire rate limit token
    await rate_limiter.acquire("vnstock")
    
    try:
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None, 
            partial(_fetch_ohlcv_sync, symbol, start, end)
        )
        
        if df is None or df.empty:
            logger.warning(
                "No OHLCV data returned from vnstock",
                symbol=symbol,
                start=start,
                end=end
            )
            return []
        
        # Convert DataFrame to list of dicts
        records = df.to_dict(orient="records")
        
        # Standardize column names
        standardized = []
        for record in records:
            std_record = {
                "ts": record.get("time") or record.get("date"),
                "open": record.get("open"),
                "high": record.get("high"),
                "low": record.get("low"),
                "close": record.get("close"),
                "volume": record.get("volume")
            }
            standardized.append(std_record)
        
        logger.info(
            "Fetched OHLCV from vnstock",
            symbol=symbol,
            records=len(standardized)
        )
        
        return standardized
        
    except ConnectionError as e:
        logger.error(
            "vnstock connection error",
            symbol=symbol,
            error=str(e)
        )
        raise
    except Exception as e:
        logger.error(
            "Error fetching OHLCV from vnstock",
            symbol=symbol,
            error=str(e)
        )
        raise


def _fetch_financials_sync(symbol: str) -> Dict[str, Any]:
    """Synchronous financial data fetch using vnstock3."""
    try:
        from vnstock3 import Vnstock
        stock = Vnstock().stock(symbol=symbol, source="TCBS")
        
        # Fetch ratios and income statement
        ratios = stock.finance.ratio(period="quarter", lang="en")
        income = stock.finance.income_statement(period="quarter", lang="en")
        
        return {
            "ratios": ratios.to_dict(orient="records") if ratios is not None else [],
            "income_statement": income.to_dict(orient="records") if income is not None else []
        }
    except Exception as e:
        logger.error(
            "vnstock financials fetch failed",
            symbol=symbol,
            error=str(e)
        )
        raise


async def fetch_financials(symbol: str) -> Dict[str, Any]:
    """
    Fetch financial reports for a Vietnamese stock asynchronously.
    
    Args:
        symbol: Stock ticker (e.g., "VNM", "VIC", "FPT")
        
    Returns:
        Dictionary with 'ratios' and 'income_statement' keys
    """
    # Validate symbol
    if not await validate_symbol(symbol):
        raise ValueError(f"Invalid or unsupported symbol: {symbol}")
    
    # Acquire rate limit token
    await rate_limiter.acquire("vnstock")
    
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(_fetch_financials_sync, symbol)
        )
        
        logger.info(
            "Fetched financials from vnstock",
            symbol=symbol,
            ratios_count=len(result.get("ratios", [])),
            income_count=len(result.get("income_statement", []))
        )
        
        return result
        
    except ConnectionError as e:
        logger.error(
            "vnstock connection error for financials",
            symbol=symbol,
            error=str(e)
        )
        # Return empty result on connection error
        return {"ratios": [], "income_statement": []}
    except Exception as e:
        logger.error(
            "Error fetching financials from vnstock",
            symbol=symbol,
            error=str(e)
        )
        raise


async def get_all_symbols() -> List[str]:
    """Get list of all valid HOSE/HNX symbols."""
    cache_key = "all_symbols"
    
    if cache_key in _symbol_cache:
        return _symbol_cache[cache_key]
    
    try:
        from vnstock3 import Vnstock
        
        loop = asyncio.get_event_loop()
        
        def _get_symbols():
            stock = Vnstock().stock(source="TCBS")
            # Get listing data
            listing = stock.listing.all_symbols()
            return listing["ticker"].tolist() if listing is not None else []
        
        symbols = await loop.run_in_executor(None, _get_symbols)
        _symbol_cache[cache_key] = symbols
        
        logger.info(
            "Loaded symbol list from vnstock",
            count=len(symbols)
        )
        
        return symbols
        
    except Exception as e:
        logger.error(
            "Failed to load symbol list from vnstock",
            error=str(e)
        )
        # Return common symbols as fallback
        return ["VNM", "VIC", "FPT", "SSI", "HPG", "MWG", "VCB", "BID", "CTG", "GAS"]


async def validate_symbol(symbol: str) -> bool:
    """
    Validate if a symbol is a valid Vietnamese stock ticker.
    
    Args:
        symbol: Stock ticker to validate
        
    Returns:
        True if symbol is valid
    """
    if not symbol or not isinstance(symbol, str):
        return False
    
    symbol = symbol.upper().strip()
    
    # Quick validation: VN symbols are 3-4 uppercase letters
    if not symbol.isalpha() or len(symbol) < 2 or len(symbol) > 5:
        return False
    
    # Check against full list
    valid_symbols = await get_all_symbols()
    return symbol in valid_symbols


async def sleep_between_tickers():
    """Sleep for configured time between ticker fetches."""
    await asyncio.sleep(settings.vnstock_sleep_between_tickers)
