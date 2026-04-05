"""APScheduler-based data ingestion scheduler."""
import asyncio
import os
import sys
from pathlib import Path 
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import structlog

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from scraper.jobs.crypto_job import run_crypto_job
from scraper.jobs.stablecoin_job import run_stablecoin_job
from scraper.jobs.vn_stock_job import run_vn_stock_job

logger = structlog.get_logger()


def setup_scheduler() -> AsyncIOScheduler:
    """Configure and return the APScheduler instance."""
    scheduler = AsyncIOScheduler()
    
    # Crypto job: every 15 minutes
    scheduler.add_job(
        run_crypto_job,
        trigger=IntervalTrigger(minutes=15),
        id="crypto_job",
        name="Fetch crypto OHLCV data",
        replace_existing=True,
        misfire_grace_time=300
    )
    
    # Stablecoin job: every 30 minutes
    scheduler.add_job(
        run_stablecoin_job,
        trigger=IntervalTrigger(minutes=30),
        id="stablecoin_job",
        name="Fetch stablecoin OHLCV data",
        replace_existing=True,
        misfire_grace_time=300
    )
    
    # VN Stock job: daily at 17:15 ICT (09:15 UTC)
    scheduler.add_job(
        run_vn_stock_job,
        trigger=CronTrigger(hour=9, minute=15),
        id="vn_stock_job",
        name="Fetch VN stock data and financials",
        replace_existing=True,
        misfire_grace_time=3600
    )
    
    logger.info(
        "Scheduler configured",
        jobs=[
            {"id": "crypto_job", "interval": "15min"},
            {"id": "stablecoin_job", "interval": "30min"},
            {"id": "vn_stock_job", "cron": "0 9:15"}
        ]
    )
    
    return scheduler


async def run_initial_jobs():
    """Run all jobs once at startup."""
    logger.info("Running initial data fetch jobs")
    
    try:
        await run_crypto_job()
        logger.info("Initial crypto job completed")
    except Exception as e:
        logger.error("Initial crypto job failed", error=str(e))
    
    await asyncio.sleep(2)  # Brief pause between jobs
    
    try:
        await run_stablecoin_job()
        logger.info("Initial stablecoin job completed")
    except Exception as e:
        logger.error("Initial stablecoin job failed", error=str(e))
    
    await asyncio.sleep(2)
    
    try:
        await run_vn_stock_job()
        logger.info("Initial VN stock job completed")
    except Exception as e:
        logger.error("Initial VN stock job failed", error=str(e))


async def main():
    """Main entry point for the scheduler."""
    logger.info(
        "Starting scraper scheduler",
        timestamp=datetime.utcnow().isoformat()
    )
    
    # Setup scheduler
    scheduler = setup_scheduler()
    
    # Run initial jobs
    await run_initial_jobs()
    
    # Start scheduler
    scheduler.start()
    logger.info("Scheduler started successfully")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(60)
            # Log heartbeat
            logger.debug(
                "Scheduler heartbeat",
                running_jobs=len(scheduler.get_jobs())
            )
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
