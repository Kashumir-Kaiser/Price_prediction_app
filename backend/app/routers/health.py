"""Health check router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis
import structlog

from app.db.database import get_db
from app.config import get_settings
settings = get_settings()

logger = structlog.get_logger()
router = APIRouter()


@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.
    
    Returns:
        Health status with DB and Redis connectivity
    """
    health_status = {
        "status": "ok",
        "db": "unknown",
        "redis": "unknown"
    }
    
    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        row = result.fetchone()
        health_status["db"] = "ok"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        health_status["db"] = "error"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        r = redis.from_url(settings.redis_url)
        await r.ping()
        await r.close()
        health_status["redis"] = "ok"
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        health_status["redis"] = "error"
        health_status["status"] = "degraded"
    
    # Return appropriate status code
    if health_status["status"] != "ok":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check for Kubernetes/Docker.
    
    Returns:
        Ready status
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail={"ready": False})


@router.get("/live")
async def liveness_check():
    """
    Liveness check for Kubernetes/Docker.
    
    Returns:
        Alive status
    """
    return {"alive": True}
