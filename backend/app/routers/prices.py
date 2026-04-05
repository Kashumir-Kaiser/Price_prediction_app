"""Prices API router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel
import structlog

from app.db.database import get_db
from app.db import crud
from app.services.alpaca_service import fetch_bars, fetch_latest_bars, CRYPTO_SYMBOLS, STABLE_SYMBOLS
from app.services.vnstock_service import fetch_ohlcv, fetch_financials, validate_symbol

logger = structlog.get_logger()
router = APIRouter()


# Response models
class CryptoBarResponse(BaseModel):
    symbol: str
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: Optional[float] = None


class StockBarResponse(BaseModel):
    symbol: str
    ts: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class FinancialsResponse(BaseModel):
    symbol: str
    period: str
    report_type: str
    data: dict


# Crypto endpoints
@router.get("/crypto/latest")
async def get_crypto_latest(db: AsyncSession = Depends(get_db)):
    """
    Get latest bars for all crypto and stablecoin symbols.
    
    Returns:
        List of latest bars for BTC, ETH, SOL, USDT, USDC
    """
    try:
        # Try to get from database first
        all_symbols = CRYPTO_SYMBOLS + STABLE_SYMBOLS
        bars = await crud.get_latest_crypto_bars(db, all_symbols)
        
        if not bars:
            # Fallback: fetch from API
            logger.info("No cached bars found, fetching from Alpaca")
            latest = await fetch_latest_bars(all_symbols)
            return {
                "source": "alpaca",
                "data": latest
            }
        
        return {
            "source": "database",
            "data": [
                {
                    "symbol": bar.symbol,
                    "ts": bar.ts.isoformat(),
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": float(bar.volume),
                    "vwap": float(bar.vwap) if bar.vwap else None
                }
                for bar in bars
            ]
        }
    except Exception as e:
        logger.error("Error fetching latest crypto bars", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crypto/history")
async def get_crypto_history(
    symbol: str = Query(..., description="Crypto symbol (e.g., BTC/USD)"),
    timeframe: str = Query("1Day", description="Timeframe (1Min, 15Min, 1Hour, 1Day)"),
    start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical OHLCV bars for a cryptocurrency.
    
    Returns:
        List of historical bars
    """
    try:
        # Validate symbol
        all_symbols = CRYPTO_SYMBOLS + STABLE_SYMBOLS
        if symbol not in all_symbols:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid symbol. Supported: {all_symbols}"
            )
        
        # Parse dates
        start_dt = None
        end_dt = None
        if start:
            start_dt = datetime.strptime(start, "%Y-%m-%d")
        if end:
            end_dt = datetime.strptime(end, "%Y-%m-%d")
        
        # Try database first
        bars = await crud.get_crypto_bars(db, symbol, start=start_dt, end=end_dt, limit=1000)
        
        if len(bars) >= 30:  # Sufficient data in DB
            return {
                "symbol": symbol,
                "source": "database",
                "count": len(bars),
                "data": [
                    {
                        "ts": bar.ts.isoformat(),
                        "open": float(bar.open),
                        "high": float(bar.high),
                        "low": float(bar.low),
                        "close": float(bar.close),
                        "volume": float(bar.volume)
                    }
                    for bar in bars
                ]
            }
        
        # Fetch from API
        logger.info("Fetching crypto history from Alpaca", symbol=symbol)
        bars = await fetch_bars(symbol, timeframe, start, end)
        
        return {
            "symbol": symbol,
            "source": "alpaca",
            "count": len(bars),
            "data": bars
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching crypto history", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Stock endpoints
@router.get("/stocks/latest")
async def get_stock_latest(
    symbol: str = Query(..., description="Stock symbol (e.g., VNM)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get latest price for a Vietnamese stock.
    
    Returns:
        Latest stock bar
    """
    try:
        # Validate symbol
        if not await validate_symbol(symbol):
            raise HTTPException(status_code=422, detail=f"Invalid symbol: {symbol}")
        
        # Get from database
        bars = await crud.get_stock_bars(db, symbol, limit=1)
        
        if bars:
            bar = bars[0]
            return {
                "symbol": symbol,
                "source": "database",
                "data": {
                    "ts": bar.ts.isoformat(),
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": int(bar.volume)
                }
            }
        
        # Fetch from API
        logger.info("Fetching stock from vnstock", symbol=symbol)
        end = date.today()
        start = end - timedelta(days=7)
        bars = await fetch_ohlcv(symbol, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        
        if not bars:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        return {
            "symbol": symbol,
            "source": "vnstock",
            "data": bars[-1]  # Latest bar
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching stock latest", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/history")
async def get_stock_history(
    symbol: str = Query(..., description="Stock symbol (e.g., VNM)"),
    start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical OHLCV for a Vietnamese stock.
    
    Returns:
        List of historical bars
    """
    try:
        # Validate symbol
        if not await validate_symbol(symbol):
            raise HTTPException(status_code=422, detail=f"Invalid symbol: {symbol}")
        
        # Parse dates
        start_dt = None
        end_dt = None
        if start:
            start_dt = datetime.strptime(start, "%Y-%m-%d").date()
        else:
            start_dt = date.today() - timedelta(days=365 * 2)  # Default 2 years
        
        if end:
            end_dt = datetime.strptime(end, "%Y-%m-%d").date()
        else:
            end_dt = date.today()
        
        # Try database first
        bars = await crud.get_stock_bars(db, symbol, start=start_dt, end=end_dt, limit=1000)
        
        if len(bars) >= 30:
            return {
                "symbol": symbol,
                "source": "database",
                "count": len(bars),
                "data": [
                    {
                        "ts": bar.ts.isoformat(),
                        "open": float(bar.open),
                        "high": float(bar.high),
                        "low": float(bar.low),
                        "close": float(bar.close),
                        "volume": int(bar.volume)
                    }
                    for bar in bars
                ]
            }
        
        # Fetch from API
        logger.info("Fetching stock history from vnstock", symbol=symbol)
        bars = await fetch_ohlcv(symbol, start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d"))
        
        return {
            "symbol": symbol,
            "source": "vnstock",
            "count": len(bars),
            "data": bars
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching stock history", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/financials")
async def get_stock_financials(
    symbol: str = Query(..., description="Stock symbol (e.g., VNM)"),
    period: Optional[str] = Query(None, description="Period filter (e.g., 2024Q3)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get financial reports for a Vietnamese stock.
    
    Returns:
        Financial ratios and income statement data
    """
    try:
        # Validate symbol
        if not await validate_symbol(symbol):
            raise HTTPException(status_code=422, detail=f"Invalid symbol: {symbol}")
        
        # Try database first
        reports = await crud.get_financials(db, symbol, period)
        
        if reports and len(reports) > 0:
            return {
                "symbol": symbol,
                "source": "database",
                "data": {
                    "ratios": [r.data for r in reports if r.report_type == "ratio"],
                    "income_statement": [r.data for r in reports if r.report_type == "income"]
                }
            }
        
        # Fetch from API
        logger.info("Fetching financials from vnstock", symbol=symbol)
        financials = await fetch_financials(symbol)
        
        return {
            "symbol": symbol,
            "source": "vnstock",
            "data": financials
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching financials", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
