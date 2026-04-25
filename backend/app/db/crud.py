"""CRUD operations for database models."""
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CryptoBar, StockBar


async def get_crypto_bars(
    db: AsyncSession,
    symbol: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 1000,
) -> List[CryptoBar]:
    """Get crypto OHLCV bars for a symbol."""
    query = select(CryptoBar).where(CryptoBar.symbol == symbol)
    if start:
        query = query.where(CryptoBar.ts >= start)
    if end:
        query = query.where(CryptoBar.ts <= end)

    query = query.order_by(desc(CryptoBar.ts)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def upsert_crypto_bar(db: AsyncSession, symbol: str, bar_data: Dict[str, Any]) -> CryptoBar:
    """Upsert a crypto bar."""
    existing = await db.execute(
        select(CryptoBar).where(
            CryptoBar.symbol == symbol,
            CryptoBar.ts == bar_data["ts"],
        )
    )
    existing = existing.scalar_one_or_none()

    if existing:
        for key, value in bar_data.items():
            setattr(existing, key, value)
        await db.flush()
        return existing

    new_bar = CryptoBar(symbol=symbol, **bar_data)
    db.add(new_bar)
    await db.flush()
    return new_bar


async def get_latest_crypto_bars(db: AsyncSession, symbols: List[str]) -> List[CryptoBar]:
    """Get latest bar for each symbol."""
    result = await db.execute(
        select(CryptoBar)
        .where(CryptoBar.symbol.in_(symbols))
        .order_by(CryptoBar.symbol, desc(CryptoBar.ts))
        .distinct(CryptoBar.symbol)
    )
    return result.scalars().all()


async def get_stock_bars(
    db: AsyncSession,
    symbol: str,
    start: Optional[date] = None,
    end: Optional[date] = None,
    limit: int = 1000,
) -> List[StockBar]:
    """Get stock OHLCV bars for a symbol."""
    query = select(StockBar).where(StockBar.symbol == symbol)
    if start:
        query = query.where(StockBar.ts >= start)
    if end:
        query = query.where(StockBar.ts <= end)

    query = query.order_by(desc(StockBar.ts)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def upsert_stock_bar(db: AsyncSession, symbol: str, bar_data: Dict[str, Any]) -> StockBar:
    """Upsert a stock bar."""
    existing = await db.execute(
        select(StockBar).where(
            StockBar.symbol == symbol,
            StockBar.ts == bar_data["ts"],
        )
    )
    existing = existing.scalar_one_or_none()

    if existing:
        for key, value in bar_data.items():
            setattr(existing, key, value)
        await db.flush()
        return existing

    new_bar = StockBar(symbol=symbol, **bar_data)
    db.add(new_bar)
    await db.flush()
    return new_bar
