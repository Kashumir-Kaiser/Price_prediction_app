"""Stablecoin data ingestion job."""
import asyncio
import sys
import os
from datetime import datetime, timedelta
import structlog

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.services.alpaca_service import fetch_bars, check_stablecoin_deviation, STABLE_SYMBOLS
from backend.app.db.database import AsyncSessionLocal
from backend.app.db import crud

logger = structlog.get_logger()


async def run_stablecoin_job():
    """
    Fetch latest 1-day bars for stablecoins.
    Runs every 30 minutes.
    Flags significant deviations from $1.00.
    """
    logger.info("Starting stablecoin job")
    
    async with AsyncSessionLocal() as db:
        try:
            end = datetime.utcnow()
            start = end - timedelta(days=2)
            
            total_upserted = 0
            deviations = []
            
            for symbol in STABLE_SYMBOLS:
                try:
                    logger.debug("Fetching stablecoin bars", symbol=symbol)
                    
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
                        
                        # Check for deviation
                        if check_stablecoin_deviation(bar, threshold=0.005):
                            deviation = abs(bar["c"] - 1.0)
                            deviations.append({
                                "symbol": symbol,
                                "close": bar["c"],
                                "deviation": deviation
                            })
                            logger.warning(
                                "Stablecoin deviation detected",
                                symbol=symbol,
                                close=bar["c"],
                                deviation=deviation
                            )
                        
                        await crud.upsert_crypto_bar(db, symbol, bar_data)
                        total_upserted += 1
                    
                    logger.debug(
                        "Upserted stablecoin bars",
                        symbol=symbol,
                        count=len(bars)
                    )
                    
                except Exception as e:
                    logger.error(
                        "Error processing stablecoin symbol",
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
                await r.publish("market_updates", "stablecoin_updated")
                if deviations:
                    await r.publish("alerts", f"stablecoin_deviations: {len(deviations)}")
                await r.close()
            except Exception as e:
                logger.warning("Failed to publish Redis event", error=str(e))
            
            logger.info(
                "Stablecoin job completed",
                symbols=len(STABLE_SYMBOLS),
                total_upserted=total_upserted,
                deviations=len(deviations)
            )
            
        except Exception as e:
            logger.error("Stablecoin job failed", error=str(e))
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(run_stablecoin_job())
