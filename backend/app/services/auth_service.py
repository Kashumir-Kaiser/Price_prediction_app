"""Authentication service with password hashing and JWT."""
from datetime import datetime, timedelta

import bcrypt as _bcrypt

from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import User
from app.config import get_settings

settings = get_settings()
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Password helpers
def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = _bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    return _bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")
 
 
def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# JWT helpers
def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload["iat"] = datetime.utcnow()
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
 
 
def decode_token(token: str) -> dict:
    """Decode a JWT token. Raises JWTError on invalid/expired token."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


# DB helpers
async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """Get user by username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()
 
 
async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Get user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()
 
 
async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    role: str = "user",
) -> User:
    """Create a new user with a hashed password."""
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
 
 
async def update_last_login(db: AsyncSession, user: User) -> None:
    """Update user's last login timestamp."""
    user.last_login_at = datetime.utcnow()
    await db.commit()
