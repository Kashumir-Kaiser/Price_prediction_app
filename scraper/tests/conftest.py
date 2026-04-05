"""Pytest setup for scraper tests."""
import os
import sys

import pytest
import redis as redis_lib
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command

# Ensure repository root is importable during test collection.
repo_root    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
backend_root = os.path.join(repo_root, "backend")
sys.path.insert(0, repo_root)
sys.path.insert(0, backend_root)


# ──────────────────────────────────────────────────────────────────────────────
# Connection helpers
# ──────────────────────────────────────────────────────────────────────────────

def _pg_test_url() -> str:
    host     = os.environ.get("POSTGRES_HOST", "localhost")
    port     = os.environ.get("POSTGRES_PORT", "5432")
    user     = os.environ.get("POSTGRES_USER", "market_user")
    password = os.environ.get("POSTGRES_PASSWORD", "change_me_in_production")
    db       = os.environ.get("POSTGRES_DB", "market_db_test")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/1")


# ──────────────────────────────────────────────────────────────────────────────
# Database fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def db_engine():
    """
    SQLAlchemy engine pointed at market_db_test.
    Re-uses the same Alembic migrations as the backend (path resolved via
    backend_root so the scraper doesn't need its own alembic setup).
    Schema is dropped after the full test session.
    """
    engine = create_engine(_pg_test_url(), echo=False, future=True)

    alembic_cfg = Config(os.path.join(backend_root, "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", _pg_test_url())
    command.upgrade(alembic_cfg, "head")

    yield engine

    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        conn.commit()

    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    """
    Yields a real SQLAlchemy Session against market_db_test.
    Rolled back after every test — no data leaks between tests.
    """
    connection  = db_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ──────────────────────────────────────────────────────────────────────────────
# Redis fixture
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def redis_client():
    """
    Redis client pointed at DB index 1 (test keyspace, per docker-compose).
    Flushed before and after each test.
    """
    client = redis_lib.from_url(REDIS_URL, decode_responses=True)
    client.flushdb()
    yield client
    client.flushdb()
    client.close()