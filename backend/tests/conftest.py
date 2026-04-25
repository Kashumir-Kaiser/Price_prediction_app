"""Pytest configuration and fixtures."""
import os
import sys

import numpy as np
import pandas as pd
import pytest
import redis as redis_lib
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, Mock

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from alembic.config import Config
from alembic import command

# Make the project root importable when running tests from the tests/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytest_plugins = ["pytest_asyncio"]


# ──────────────────────────────────────────────────────────────────────────────
# Connection helpers
# ──────────────────────────────────────────────────────────────────────────────

def _pg_test_url() -> str:
    host     = os.environ.get("POSTGRES_HOST", "localhost")
    port     = os.environ.get("POSTGRES_PORT", "5432")
    user     = os.environ.get("POSTGRES_USER", "market_user")
    password = os.environ.get("POSTGRES_PASSWORD", "change_me_in_production")
    db       = os.environ.get("POSTGRES_DB", "market_db_test")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


def _pg_test_sync_url() -> str:
    host     = os.environ.get("POSTGRES_HOST", "localhost")
    port     = os.environ.get("POSTGRES_PORT", "5432")
    user     = os.environ.get("POSTGRES_USER", "market_user")
    password = os.environ.get("POSTGRES_PASSWORD", "change_me_in_production")
    db       = os.environ.get("POSTGRES_DB", "market_db_test")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/1")


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI dependency overrides (unit tests — no real DB or rate-limiter)
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _override_dependencies(request):
    """
    Replace two FastAPI dependencies for every test in the suite.

    1. get_db  — yields a mocked AsyncSession so no test ever dials the real
       PostgreSQL.  db.add is a plain Mock because SQLAlchemy's AsyncSession.add
       is *synchronous*; keeping it as AsyncMock produces "coroutine was never
       awaited" RuntimeWarnings.

    2. auth_rate_limiter — replaced with a no-op coroutine so login tests never
       touch TokenBucket and never hit the 'token' vs 'tokens' kwarg bug in the
       production rate-limiter code.

    Tests that need a *real* database connection should use the `db_session`
    fixture, which bypasses this override via app.dependency_overrides directly.
    """
    # Integration tests should use real infra fixtures, not mocked dependencies.
    node_path = str(request.node.fspath).replace("\\", "/")
    if "/tests/integration/" in node_path:
        yield
        return

    from app.main import app
    from app.db.database import get_db
    from app.utils.rate_limiter import auth_rate_limiter

    mock_db = AsyncMock()
    mock_db.add = Mock()
    _default_result = Mock()
    _default_result.scalars.return_value.first.return_value = None
    _default_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = _default_result

    async def _fake_get_db():
        yield mock_db

    async def _noop_rate_limit():
        return None

    app.dependency_overrides[get_db] = _fake_get_db
    app.dependency_overrides[auth_rate_limiter] = _noop_rate_limit

    yield

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(auth_rate_limiter, None)


# ──────────────────────────────────────────────────────────────────────────────
# Real database fixtures (integration tests — opt-in, not autouse)
#
# Usage in a test:
#
#   def test_something(db_session):       # real postgres, rolled back after test
#       ...
#   def test_cache(redis_client):         # real redis index 1, flushed around test
#       ...
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def db_engine():
    """
    SQLAlchemy engine pointed at market_db_test.
    Runs Alembic migrations once per session, drops the schema on teardown.
    """
    engine = create_async_engine(_pg_test_url(), echo=False, future=True)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", _pg_test_sync_url())
    command.upgrade(alembic_cfg, "head")

    yield engine

    cleanup_engine = create_engine(_pg_test_sync_url(), future=True)
    with cleanup_engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        conn.commit()
    cleanup_engine.dispose()


@pytest.fixture()
async def db_session(db_engine, _override_dependencies):
    """
    Yields a real SQLAlchemy Session against market_db_test.
    Every test is wrapped in a transaction that is rolled back on teardown —
    nothing written during the test survives to the next one.

    Also wires the session into FastAPI's get_db override so HTTP-level
    integration tests hit the same rolled-back transaction.
    """
    from app.main import app
    from app.db.database import get_db

    connection = await db_engine.connect()
    transaction = await connection.begin()
    SessionLocal = async_sessionmaker(
        bind=connection,
        expire_on_commit=False,
        autoflush=False,
    )
    session = SessionLocal()

    # Override get_db so TestClient requests share the same transaction.
    async def _real_get_db():
        yield session

    app.dependency_overrides[get_db] = _real_get_db

    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()

    # Restore the mock override that _override_dependencies installed.
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def redis_client():
    """
    Redis client pointed at DB index 1 (test keyspace).
    Flushed before and after each test.
    """
    client = redis_lib.from_url(REDIS_URL, decode_responses=True)
    client.flushdb()
    yield client
    client.flushdb()
    client.close()


@pytest.fixture()
async def client(db_session):
    """
    Async HTTP client for integration tests.
    Uses the app with dependency overrides already configured by db_session.
    """
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client


# ──────────────────────────────────────────────────────────────────────────────
# Domain fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_alpaca_response():
    """Mock Alpaca API response."""
    return {
        "bars": {
            "BTC/USD": [
                {
                    "t": "2024-01-01T00:00:00Z",
                    "o": 42000.0,
                    "h": 43000.0,
                    "l": 41000.0,
                    "c": 42500.0,
                    "v": 1000.0,
                    "vw": 42200.0,
                },
                {
                    "t": "2024-01-02T00:00:00Z",
                    "o": 42500.0,
                    "h": 43500.0,
                    "l": 42000.0,
                    "c": 43000.0,
                    "v": 1200.0,
                    "vw": 42800.0,
                },
            ]
        },
        "next_page_token": None,
    }


@pytest.fixture
def mock_vnstock_data():
    """Mock vnstock DataFrame."""
    return pd.DataFrame(
        {
            "time":   ["2024-01-01", "2024-01-02", "2024-01-03"],
            "open":   [100.0, 102.0, 101.0],
            "high":   [105.0, 107.0, 106.0],
            "low":    [98.0,  100.0,  99.0],
            "close":  [102.0, 105.0, 104.0],
            "volume": [1_000_000, 1_200_000, 1_100_000],
        }
    )


@pytest.fixture
def sample_ohlcv_data():
    """
    100-row OHLCV DataFrame sufficient for all technical-indicator tests.
    Seeded random walk — identical values on every test run.
    """
    rng = np.random.default_rng(42)
    n = 100
    dates = pd.date_range("2024-01-01", periods=n, freq="D")

    close = 100.0 + np.cumsum(rng.normal(0, 0.5, n))
    close = np.maximum(close, 1.0)

    noise     = rng.normal(0, 0.002, n)
    up_wick   = np.abs(rng.normal(0, 0.005, n))
    down_wick = np.abs(rng.normal(0, 0.005, n))

    return pd.DataFrame(
        {
            "ts":     dates,
            "open":   close * (1 + noise),
            "high":   close * (1 + up_wick),
            "low":    close * (1 - down_wick),
            "close":  close,
            "volume": rng.integers(1_000, 10_000, n).astype(float),
        }
    )
