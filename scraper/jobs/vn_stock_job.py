"""Vietnamese stock data ingestion job."""
import asyncio
import os
from datetime import datetime, date, timedelta
import structlog

from backend.app.services.vnstock_service import (
    fetch_ohlcv, fetch_financials, get_all_symbols, sleep_between_tickers
)
from backend.app.db.database import AsyncSessionLocal
from backend.app.db import crud

logger = structlog.get_logger()

# Default VN stocks to track (can be extended via watchlist)
DEFAULT_VN_SYMBOLS = ["VNM", "VIC", "FPT", "SSI", "HPG", "MWG", "VCB", "BID", "CTG", "GAS"]


async def run_vn_stock_job():
    """
    Fetch OHLCV and financials for Vietnamese stocks.
    Runs daily at 17:15 ICT (09:15 UTC).
    """
    logger.info("Starting VN stock job")
    
    async with AsyncSessionLocal() as db:
        try:
            # Get symbols from watchlist or use defaults
            watchlist = await crud.get_watchlist(db, asset_type="stock")
            if watchlist:
                symbols = [w.symbol for w in watchlist]
            else:
                symbols = DEFAULT_VN_SYMBOLS
                # Add defaults to watchlist
                for sym in symbols:
                    await crud.add_to_watchlist(db, sym, "stock")
            
            end = date.today()
            start = end - timedelta(days=30)  # Last 30 days
            
            total_ohlcv = 0
            total_financials = 0
            
            for symbol in symbols:
                try:
                    logger.debug("Fetching VN stock data", symbol=symbol)
                    
                    # Fetch OHLCV
                    bars = await fetch_ohlcv(
                        symbol=symbol,
                        start=start.strftime("%Y-%m-%d"),
                        end=end.strftime("%Y-%m-%d")
                    )
                    
                    for bar in bars:
                        bar_data = {
                            "ts": bar["ts"] if isinstance(bar["ts"], date) else datetime.strptime(bar["ts"], "%Y-%m-%d").date(),
                            "open": bar["open"],
                            "high": bar["high"],
                            "low": bar["low"],
                            "close": bar["close"],
                            "volume": bar["volume"]
                        }
                        
                        await crud.upsert_stock_bar(db, symbol, bar_data)
                        total_ohlcv += 1
                    
                    logger.debug(
                        "Upserted VN stock bars",
                        symbol=symbol,
                        count=len(bars)
                    )
                    
                    # Fetch financials (quarterly)
                    try:
                        financials = await fetch_financials(symbol)
                        
                        # Process ratios
                        for ratio_data in financials.get("ratios", []):
                            if isinstance(ratio_data, dict) and "period" in ratio_data:
                                await crud.upsert_financial_report(
                                    db, symbol, ratio_data["period"], "ratio", ratio_data
                                )
                                total_financials += 1
                        
                        # Process income statements
                        for income_data in financials.get("income_statement", []):
                            if isinstance(income_data, dict) and "period" in income_data:
                                await crud.upsert_financial_report(
                                    db, symbol, income_data["period"], "income", income_data
                                )
                                total_financials += 1
                        
                        logger.debug(
                            "Upserted VN financials",
                            symbol=symbol,
                            ratios=len(financials.get("ratios", [])),
                            income=len(financials.get("income_statement", []))
                        )
                        
                    except Exception as e:
                        logger.warning(
                            "Error fetching financials",
                            symbol=symbol,
                            error=str(e)
                        )
                    
                    # Sleep between tickers to respect rate limits
                    await sleep_between_tickers()
                    
                except Exception as e:
                    logger.error(
                        "Error processing VN stock symbol",
                        symbol=symbol,
                        error=str(e)
                    )
                    continue
            
            await db.commit()
            
            # Publish update event to Redis
            try:
                import redis.asyncio as redis
                from backend.app.config import settings
                
                r = redis.from_url(settings.redis_url)
                await r.publish("market_updates", "vn_stocks_updated")
                await r.close()
            except Exception as e:
                logger.warning("Failed to publish Redis event", error=str(e))
            
            logger.info(
                "VN stock job completed",
                symbols=len(symbols),
                total_ohlcv=total_ohlcv,
                total_financials=total_financials
            )
            
        except Exception as e:
            logger.error("VN stock job failed", error=str(e))
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(run_vn_stock_job())
