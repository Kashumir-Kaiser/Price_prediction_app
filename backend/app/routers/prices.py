"""Prices router for fetching price data."""
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import structlog

from app.db.database import get_db
from app.db import crud
from app.routers.auth import get_current_active_user
from app.db.models import User

router = APIRouter()
logger = structlog.get_logger()

@router.get("/prices")
async def get_prices(
    symbol: str = Query(...),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get historical OHLCV data for a symbol."""
    logger.info("Fetching prices", symbol=symbol, start=start, end=end)
    try:
        if "/" in symbol:
            bars = await crud.get_crypto_bars(db, symbol, start=start, end=end)
        else:
            bars = await crud.get_stock_bars(db, symbol, start=start, end=end)
        
        data = [
            {
                "ts": bar.ts.isoformat() if bar.ts else None,
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": float(bar.volume),
            }
            for bar in bars
        ]
        return {"data": data}
    except Exception as e:
        logger.error("Failed to fetch prices", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch price data")