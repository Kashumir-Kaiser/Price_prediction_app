"""Authentication router with login and register endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, constr
from jose import JWTError

from app.db.database import get_db
from app.db.models import User
from app.services.auth_service import (
    get_user_by_username,
    create_user,
    verify_password,
    create_access_token,
    decode_token,
    update_last_login,
)
from app.utils.sanitiser import sanitise_identifier
from app.utils.rate_limiter import auth_rate_limiter

router = APIRouter(tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Schemas
class RegisterRequest(BaseModel):
    """Registration request schema with validation."""
    username: constr(min_length=3, max_length=64, pattern=r'^[a-zA-Z0-9_]+$')
    email: EmailStr
    password: constr(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    role: str


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    username: str
    email: str
    role: str


# Endpoints
@router.post("/register", response_model=UserResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check if username already exists
    if await get_user_by_username(db, body.username):
        raise HTTPException(status_code=409, detail="Username already taken")

    # Check if email already exists
    existing_email = await db.execute(
        select(User).where(User.email == body.email)
    )
    if existing_email.scalars().first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = await create_user(db, body.username, body.email, body.password)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(auth_rate_limiter),  # Rate limit: 10 attempts/min per IP
):
    """Login and get JWT access token."""
    # Sanitize username input (SQL injection protection)
    username = sanitise_identifier(form.username, "username")

    user = await get_user_by_username(db, username)
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    # Update last login
    await update_last_login(db, user)

    token = create_access_token({"sub": user.username, "role": user.role})
    return TokenResponse(access_token=token, role=user.role)


# Current-user dependency (reuse in other routers)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        if not username:
            raise ValueError("Invalid token payload")
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )

    user = await get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency: any authenticated, active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency: ADMIN ONLY.
    Inject into any route that must be restricted to admin users.
    Returns HTTP 403 Forbidden for role != 'admin'.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )
    return current_user
