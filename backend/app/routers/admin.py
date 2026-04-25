"""Admin-only router with RBAC enforcement."""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import structlog

from app.db.database import get_db
from app.db.models import User, RequestLog
from app.routers.auth import require_admin

router = APIRouter()
logger = structlog.get_logger()


class UpdateRoleRequest(BaseModel):
    """Update role request schema."""
    role: str = Field(..., pattern=r"^(user|admin)$")


class CreateUserRequest(BaseModel):
    """Create user request schema (admin only)."""
    username: str = Field(..., min_length=3, max_length=64, pattern=r'^[a-zA-Z0-9_]+$')
    email: str = Field(..., pattern=r'^\S+@\S+\.\S+$')
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="user", pattern=r"^(user|admin)$")
    is_active: bool = True


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str
    last_login_at: str | None


class TrafficStats(BaseModel):
    """Traffic statistics response."""
    total_requests: int
    requests_by_status: list
    requests_by_method: list
    avg_duration_ms: float
    top_paths: list
    period_days: int = 7


# All routes use require_admin dependency for RBAC

@router.get("/admin/users", response_model=list[UserResponse])
async def list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()

    return [
        UserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at.isoformat() if u.created_at else None,
            updated_at=u.updated_at.isoformat() if u.updated_at else None,
            last_login_at=u.last_login_at.isoformat() if u.last_login_at else None,
        )
        for u in users
    ]


@router.patch("/admin/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    body: UpdateRoleRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update user role (admin only). Prevents self-demotion."""
    # Prevent self-demotion
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own role.",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found.",
        )

    old_role = user.role
    user.role = body.role
    await db.commit()

    logger.info(
        "User role updated",
        admin=admin.username,
        target_user_id=user_id,
        old_role=old_role,
        new_role=body.role,
    )

    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "message": f"Role updated from '{old_role}' to '{body.role}'"
    }


@router.post("/admin/users", response_model=UserResponse, status_code=201)
async def create_user_admin(
    body: CreateUserRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user (admin only)."""
    from app.services.auth_service import hash_password

    # Check if username already exists
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken.",
        )

    # Check if email already exists
    existing_email = await db.execute(select(User).where(User.email == body.email))
    if existing_email.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
        is_active=body.is_active,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(
        "User created by admin",
        admin=admin.username,
        new_user=body.username,
        role=body.role,
    )

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None,
        updated_at=user.updated_at.isoformat() if user.updated_at else None,
        last_login_at=None,
    )


@router.get("/admin/traffic", response_model=TrafficStats)
async def get_traffic_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    period_days: int = 7,
):
    """Get traffic statistics for admin dashboard (admin only)."""
    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(days=period_days)

    # Total requests
    total_result = await db.execute(
        select(func.count(RequestLog.id)).where(RequestLog.timestamp >= cutoff)
    )
    total = total_result.scalar()

    # By status code
    status_result = await db.execute(
        select(RequestLog.status_code, func.count(RequestLog.id))
        .where(RequestLog.timestamp >= cutoff)
        .group_by(RequestLog.status_code)
    )
    by_status = [{"status_code": s, "count": c} for s, c in status_result.all()]

    # By method
    method_result = await db.execute(
        select(RequestLog.method, func.count(RequestLog.id))
        .where(RequestLog.timestamp >= cutoff)
        .group_by(RequestLog.method)
    )
    by_method = [{"method": m, "count": c} for m, c in method_result.all()]

    # Average duration
    avg_result = await db.execute(
        select(func.avg(RequestLog.duration_ms)).where(RequestLog.timestamp >= cutoff)
    )
    avg_duration = avg_result.scalar() or 0

    # Top paths
    top_result = await db.execute(
        select(RequestLog.path, func.count(RequestLog.id))
        .where(RequestLog.timestamp >= cutoff)
        .group_by(RequestLog.path)
        .order_by(func.count(RequestLog.id).desc())
        .limit(10)
    )
    top_paths = [{"path": p, "count": c} for p, c in top_result.all()]

    return TrafficStats(
        total_requests=total,
        requests_by_status=by_status,
        requests_by_method=by_method,
        avg_duration_ms=round(avg_duration, 2),
        top_paths=top_paths,
        period_days=period_days,
    )
