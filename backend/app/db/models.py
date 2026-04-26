"""SQLAlchemy ORM models."""
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Index,
    text, UniqueConstraint, BigInteger, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    """User model with authentication and RBAC."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(16), default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_role", "role"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class PriceBar(Base):
    """Price bar data (OHLCV) for any asset."""
    __tablename__ = "price_bars"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(32), nullable=False)
    ts = Column(DateTime, nullable=False)
    open = Column(Numeric(18, 8), nullable=False)
    high = Column(Numeric(18, 8), nullable=False)
    low = Column(Numeric(18, 8), nullable=False)
    close = Column(Numeric(18, 8), nullable=False)
    volume = Column(Numeric(24, 8), nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "ts", name="uq_price_bars_symbol_ts"),
        Index("idx_price_bars_symbol_ts", "symbol", "ts"),
    )


class CryptoBar(PriceBar):
    """Crypto-specific price bar (inherits from PriceBar)."""
    __tablename__ = "crypto_bars"

    id = Column(Integer, primary_key=True)


class StockBar(PriceBar):
    """Stock-specific price bar (inherits from PriceBar)."""
    __tablename__ = "stock_bars"

    id = Column(Integer, primary_key=True)


class StockDaily(Base):
    """Stock daily price bar (used by scraper)."""
    __tablename__ = "stock_daily"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(32), nullable=False)
    ts = Column(DateTime, nullable=False)
    open = Column(Numeric(18, 8), nullable=False)
    high = Column(Numeric(18, 8), nullable=False)
    low = Column(Numeric(18, 8), nullable=False)
    close = Column(Numeric(18, 8), nullable=False)
    volume = Column(Numeric(24, 8), nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "ts", name="uq_stock_daily_symbol_ts"),
        Index("idx_stock_daily_symbol_ts", "symbol", "ts"),
    )


class RequestLog(Base):
    """Traffic request log for admin analytics."""
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True)
    method = Column(String(16), nullable=False)
    path = Column(String(512), nullable=False)
    status_code = Column(Integer, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    client_ip = Column(String(64), nullable=True)
    username = Column(String(64), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_request_logs_timestamp", "timestamp"),
        Index("idx_request_logs_path", "path"),
    )
