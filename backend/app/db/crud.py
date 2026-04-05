"""CRUD operations for database models."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import structlog

from app.db.models import OHLCVCrypto, OHLCVStocks, FinancialReports, Watchlist, ModelRegistry

logger = structlog.get_logger()


# OHLCV Crypto CRUD
async def get_crypto_bars(
    db: AsyncSession,
    symbol: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 1000
) -> List[OHLCVCrypto]:
    """Get crypto OHLCV bars for a symbol."""
    query = select(OHLCVCrypto).where(OHLCVCrypto.symbol == symbol)
    
    if start:
        query = query.where(OHLCVCrypto.ts >= start)
    if end:
        query = query.where(OHLCVCrypto.ts <= end)
    
    query = query.order_by(desc(OHLCVCrypto.ts)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def upsert_crypto_bar(db: AsyncSession, symbol: str, bar_data: Dict[str, Any]) -> OHLCVCrypto:
    """Upsert a crypto bar."""
    # Check if exists
    existing = await db.execute(
        select(OHLCVCrypto).where(
            OHLCVCrypto.symbol == symbol,
            OHLCVCrypto.ts == bar_data["ts"]
        )
    )
    existing = existing.scalar_one_or_none()
    
    if existing:
        # Update
        for key, value in bar_data.items():
            setattr(existing, key, value)
        await db.flush()
        return existing
    else:
        # Insert
        new_bar = OHLCVCrypto(symbol=symbol, **bar_data)
        db.add(new_bar)
        await db.flush()
        return new_bar


async def get_latest_crypto_bars(db: AsyncSession, symbols: List[str]) -> List[OHLCVCrypto]:
    """Get latest bar for each symbol."""
    result = await db.execute(
        select(OHLCVCrypto).where(OHLCVCrypto.symbol.in_(symbols))
        .order_by(OHLCVCrypto.symbol, desc(OHLCVCrypto.ts))
        .distinct(OHLCVCrypto.symbol)
    )
    return result.scalars().all()


# OHLCV Stocks CRUD
async def get_stock_bars(
    db: AsyncSession,
    symbol: str,
    start: Optional[date] = None,
    end: Optional[date] = None,
    limit: int = 1000
) -> List[OHLCVStocks]:
    """Get stock OHLCV bars for a symbol."""
    query = select(OHLCVStocks).where(OHLCVStocks.symbol == symbol)
    
    if start:
        query = query.where(OHLCVStocks.ts >= start)
    if end:
        query = query.where(OHLCVStocks.ts <= end)
    
    query = query.order_by(desc(OHLCVStocks.ts)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def upsert_stock_bar(db: AsyncSession, symbol: str, bar_data: Dict[str, Any]) -> OHLCVStocks:
    """Upsert a stock bar."""
    existing = await db.execute(
        select(OHLCVStocks).where(
            OHLCVStocks.symbol == symbol,
            OHLCVStocks.ts == bar_data["ts"]
        )
    )
    existing = existing.scalar_one_or_none()
    
    if existing:
        for key, value in bar_data.items():
            setattr(existing, key, value)
        await db.flush()
        return existing
    else:
        new_bar = OHLCVStocks(symbol=symbol, **bar_data)
        db.add(new_bar)
        await db.flush()
        return new_bar


# Financial Reports CRUD
async def get_financials(
    db: AsyncSession,
    symbol: str,
    period: Optional[str] = None
) -> List[FinancialReports]:
    """Get financial reports for a symbol."""
    query = select(FinancialReports).where(FinancialReports.symbol == symbol)
    
    if period:
        query = query.where(FinancialReports.period == period)
    
    query = query.order_by(desc(FinancialReports.period))
    result = await db.execute(query)
    return result.scalars().all()


async def upsert_financial_report(
    db: AsyncSession,
    symbol: str,
    period: str,
    report_type: str,
    data: Dict[str, Any]
) -> FinancialReports:
    """Upsert a financial report."""
    existing = await db.execute(
        select(FinancialReports).where(
            FinancialReports.symbol == symbol,
            FinancialReports.period == period,
            FinancialReports.report_type == report_type
        )
    )
    existing = existing.scalar_one_or_none()
    
    if existing:
        existing.data = data
        existing.fetched_at = datetime.utcnow()
        await db.flush()
        return existing
    else:
        new_report = FinancialReports(
            symbol=symbol,
            period=period,
            report_type=report_type,
            data=data
        )
        db.add(new_report)
        await db.flush()
        return new_report


# Watchlist CRUD
async def get_watchlist(db: AsyncSession, asset_type: Optional[str] = None) -> List[Watchlist]:
    """Get watchlist entries."""
    query = select(Watchlist).where(Watchlist.active == True)
    
    if asset_type:
        query = query.where(Watchlist.asset_type == asset_type)
    
    result = await db.execute(query)
    return result.scalars().all()


async def add_to_watchlist(db: AsyncSession, symbol: str, asset_type: str) -> Watchlist:
    """Add symbol to watchlist."""
    existing = await db.execute(
        select(Watchlist).where(Watchlist.symbol == symbol)
    )
    existing = existing.scalar_one_or_none()
    
    if existing:
        existing.active = True
        existing.asset_type = asset_type
        await db.flush()
        return existing
    else:
        entry = Watchlist(symbol=symbol, asset_type=asset_type, active=True)
        db.add(entry)
        await db.flush()
        return entry


# Model Registry CRUD
async def get_active_model(
    db: AsyncSession,
    symbol: str,
    model_type: str
) -> Optional[ModelRegistry]:
    """Get active model for symbol and type."""
    result = await db.execute(
        select(ModelRegistry).where(
            ModelRegistry.symbol == symbol,
            ModelRegistry.model_type == model_type,
            ModelRegistry.active == True
        )
    )
    return result.scalar_one_or_none()


async def register_model(
    db: AsyncSession,
    symbol: str,
    model_type: str,
    version: int,
    metrics: Dict[str, Any],
    artifact_path: str
) -> ModelRegistry:
    """Register a new model."""
    # Deactivate existing models
    await db.execute(
        update(ModelRegistry)
        .where(
            ModelRegistry.symbol == symbol,
            ModelRegistry.model_type == model_type
        )
        .values(active=False)
    )
    
    # Register new model
    model = ModelRegistry(
        symbol=symbol,
        model_type=model_type,
        version=version,
        metrics=metrics,
        artifact_path=artifact_path,
        active=True
    )
    db.add(model)
    await db.flush()
    return model
