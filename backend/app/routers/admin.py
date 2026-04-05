"""Admin dashboard router with traffic stats and user management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_, case, desc
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import RequestLog, User
from app.routers.auth import require_admin

router = APIRouter(
    tags=["admin"],
    dependencies=[Depends(require_admin)]  # All routes require admin role
)


# Response schemas
class OverviewStats(BaseModel):
    total_requests_today: int
    unique_ips_today: int
    avg_response_ms: float
    error_rate_pct: float


class TrafficHourly(BaseModel):
    hour: str
    requests: int
    errors: int


class EndpointStats(BaseModel):
    path: str
    hits: int
    avg_duration_ms: float
    error_rate_pct: float


class UserStats(BaseModel):
    username: str
    requests_today: int
    last_seen: Optional[datetime]


class ErrorLog(BaseModel):
    method: str
    path: str
    status_code: int
    duration_ms: int
    logged_at: datetime


class UserListItem(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime]


@router.get("/stats/overview", response_model=OverviewStats)
async def get_overview_stats(db: AsyncSession = Depends(get_db)):
    """Get overview stats for today."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(
            func.count().label("total_requests"),
            func.count(func.distinct(RequestLog.client_ip)).label("unique_ips"),
            func.avg(RequestLog.duration_ms).label("avg_duration_ms"),
            (func.sum(case(
                (RequestLog.status_code >= 400, 1),
                else_=0
            )) * 100.0 / func.count()).label("error_rate_pct"),
        ).where(RequestLog.logged_at >= today_start)
    )
    row = result.one()

    return OverviewStats(
        total_requests_today=row.total_requests or 0,
        unique_ips_today=row.unique_ips or 0,
        avg_response_ms=round(row.avg_duration_ms or 0, 1),
        error_rate_pct=round(row.error_rate_pct or 0, 2),
    )


@router.get("/stats/traffic", response_model=List[TrafficHourly])
async def get_traffic_stats(db: AsyncSession = Depends(get_db)):
    """Get requests per hour for last 24 hours."""
    since = datetime.utcnow() - timedelta(hours=24)

    result = await db.execute(
        select(
            func.date_trunc('hour', RequestLog.logged_at).label("hour"),
            func.count().label("requests"),
            func.sum(case(
                (RequestLog.status_code >= 400, 1),
                else_=0
            )).label("errors"),
        )
        .where(RequestLog.logged_at >= since)
        .group_by(func.date_trunc('hour', RequestLog.logged_at))
        .order_by(func.date_trunc('hour', RequestLog.logged_at))
    )

    return [
        TrafficHourly(
            hour=row.hour.strftime("%Y-%m-%d %H:00"),
            requests=row.requests,
            errors=row.errors or 0
        )
        for row in result.all()
    ]


@router.get("/stats/endpoints", response_model=List[EndpointStats])
async def get_endpoint_stats(db: AsyncSession = Depends(get_db), limit: int = 10):
    """Get top endpoints by hit count."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(
            RequestLog.path.label("path"),
            func.count().label("hits"),
            func.avg(RequestLog.duration_ms).label("avg_duration_ms"),
            (func.sum(case(
                (RequestLog.status_code >= 400, 1),
                else_=0
            )) * 100.0 / func.count()).label("error_rate_pct"),
        )
        .where(RequestLog.logged_at >= today_start)
        .group_by(RequestLog.path)
        .order_by(desc(func.count()))
        .limit(limit)
    )

    return [
        EndpointStats(
            path=row.path,
            hits=row.hits,
            avg_duration_ms=round(row.avg_duration_ms or 0, 1),
            error_rate_pct=round(row.error_rate_pct or 0, 2),
        )
        for row in result.all()
    ]


@router.get("/stats/users", response_model=List[UserStats])
async def get_user_stats(db: AsyncSession = Depends(get_db)):
    """Get user activity stats."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(
            RequestLog.username.label("username"),
            func.count().label("requests_today"),
            func.max(RequestLog.logged_at).label("last_seen"),
        )
        .where(
            and_(
                RequestLog.logged_at >= today_start,
                RequestLog.username.isnot(None)
            )
        )
        .group_by(RequestLog.username)
        .order_by(desc(func.count()))
    )

    return [
        UserStats(
            username=row.username,
            requests_today=row.requests_today,
            last_seen=row.last_seen
        )
        for row in result.all()
    ]


@router.get("/stats/errors", response_model=List[ErrorLog])
async def get_error_logs(db: AsyncSession = Depends(get_db), limit: int = 20):
    """Get recent error requests (4xx/5xx)."""
    result = await db.execute(
        select(RequestLog)
        .where(RequestLog.status_code >= 400)
        .order_by(desc(RequestLog.logged_at))
        .limit(limit)
    )

    return [
        ErrorLog(
            method=log.method,
            path=log.path,
            status_code=log.status_code,
            duration_ms=log.duration_ms,
            logged_at=log.logged_at
        )
        for log in result.scalars().all()
    ]


@router.get("/users", response_model=List[UserListItem])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    """Get all registered users."""
    result = await db.execute(
        select(User).order_by(User.created_at.desc())
    )

    return [
        UserListItem(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )
        for user in result.scalars().all()
    ]


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Deactivate a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "admin":
        raise HTTPException(status_code=403, detail="Cannot deactivate admin users")

    user.is_active = False
    await db.commit()

    return {"message": f"User {user.username} deactivated successfully"}
