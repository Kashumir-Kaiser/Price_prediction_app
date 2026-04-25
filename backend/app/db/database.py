"""Database configuration with async engine and session factory."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import get_settings

settings = get_settings()

# Async engine for the application
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """FastAPI dependency: yield a DB session, auto-close after request."""
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()


# DEPRECATED: Do not use for production DB bootstrapping.
# Alembic migrations (upgrade head) are now the authoritative path.
# This is retained ONLY for test fixtures or temporary ephemeral DBs.
async def _create_tables_for_tests():
    """Create all tables -- FOR TESTS ONLY. Use Alembic for production."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
