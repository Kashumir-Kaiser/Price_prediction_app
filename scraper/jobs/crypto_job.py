"""Crypto data ingestion job."""
import asyncio
import os
from datetime import datetime, timedelta
import structlog

from backend.app.services.alpaca_service import fetch_bars, CRYPTO_SYMBOLS
from backend.app.db.database import AsyncSessionLocal
from backend.app.db import crud
from backend.app.utils.rate_limiter import rate_limiter

logger = structlog.get_logger()


async def run_crypto_job():
    """
    Fetch latest 1-day bars for all crypto symbols.
    Runs every 15 minutes.
    """
    logger.info("Starting crypto job")
    
    async with AsyncSessionLocal() as db:
        try:
            end = datetime.utcnow()
            start = end - timedelta(days=2)  # Fetch last 2 days to ensure coverage
            
            total_upserted = 0
            
            for symbol in CRYPTO_SYMBOLS:
                try:
                    logger.debug("Fetching crypto bars", symbol=symbol)
                    
                    bars = await fetch_bars(
                        symbol=symbol,
                        timeframe="1Day",
                        start=start.strftime("%Y-%m-%d"),
                        end=end.strftime("%Y-%m-%d"),
                        limit=1000
                    )
                    
                    for bar in bars:
                        bar_data = {
                            "ts": datetime.fromisoformat(bar["t"].replace("Z", "+00:00")),
                            "open": bar["o"],
                            "high": bar["h"],
                            "low": bar["l"],
                            "close": bar["c"],
                            "volume": bar.get("v", 0),
                            "vwap": bar.get("vw")
                        }
                        
                        await crud.upsert_crypto_bar(db, symbol, bar_data)
                        total_upserted += 1
                    
                    logger.debug(
                        "Upserted crypto bars",
                        symbol=symbol,
                        count=len(bars)
                    )
                    
                except Exception as e:
                    logger.error(
                        "Error processing crypto symbol",
                        symbol=symbol,
                        error=str(e)
                    )
                    continue
            
            await db.commit()
            
            # Publish update event to Redis
            try:
                import redis.asyncio as redis
                from backend.app.config import get_settings
                settings = get_settings()
                
                r = redis.from_url(settings.redis_url)
                await r.publish("market_updates", "crypto_updated")
                await r.close()
            except Exception as e:
                logger.warning("Failed to publish Redis event", error=str(e))
            
            logger.info(
                "Crypto job completed",
                symbols=len(CRYPTO_SYMBOLS),
                total_upserted=total_upserted
            )
            
        except Exception as e:
            logger.error("Crypto job failed", error=str(e))
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(run_crypto_job())
