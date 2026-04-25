"""Integration tests for database operations."""
import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.models import CryptoBar, StockBar


@pytest.mark.asyncio
async def test_insert_and_retrieve_crypto(db_session: AsyncSession):
    """Insert a crypto row and fetch it back."""
    stock = CryptoBar(
        symbol="BTC/USD",
        ts=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        open=42000.0,
        high=43000.0,
        low=41000.0,
        close=42500.0,
        volume=1000000.0,
    )
    db_session.add(stock)
    await db_session.commit()
    await db_session.refresh(stock)

    result = await db_session.execute(
        text("SELECT * FROM crypto_bars WHERE symbol = 'BTC/USD'")
    )
    row = result.fetchone()
    assert row is not None
    assert float(row.close) == 42500.0


@pytest.mark.asyncio
async def test_upsert_behavior_stocks(db_session: AsyncSession):
    """Two inserts with same PK: second one should update."""
    from sqlalchemy.dialects.postgresql import insert
    
    ts = datetime(2024, 1, 1).date()
    for close_price in [100.0, 200.0]:
        stmt = insert(StockBar).values(
            symbol="VCB",
            ts=ts,
            open=90.0,
            high=110.0,
            low=85.0,
            close=close_price,
            volume=500000,
        ).on_conflict_do_update(
            index_elements=["symbol", "ts"],
            set_={"close": close_price}
        )
        await db_session.execute(stmt)
        await db_session.commit()

    result = await db_session.execute(
        text("SELECT close FROM stock_bars WHERE symbol = 'VCB'")
    )
    assert float(result.scalar()) == 200.0


@pytest.mark.asyncio
async def test_multiple_symbols_crypto(db_session: AsyncSession):
    """Insert multiple crypto symbols and verify distinct rows."""
    symbols = ["BTC/USD", "ETH/USD", "SOL/USD"]
    ts = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    for sym in symbols:
        db_session.add(
            CryptoBar(
                symbol=sym,
                ts=ts,
                open=100.0,
                high=110.0,
                low=95.0,
                close=105.0,
                volume=1000000.0,
            )
        )
    await db_session.commit()

    result = await db_session.execute(
        text("SELECT COUNT(*) FROM crypto_bars WHERE symbol IN ('BTC/USD', 'ETH/USD', 'SOL/USD')")
    )
    assert result.scalar() == 3
