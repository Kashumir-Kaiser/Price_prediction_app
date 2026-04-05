"""SQLAlchemy ORM models."""
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Numeric, BigInteger,
    JSON, Boolean, UniqueConstraint, Index,          # ← Index added to imports
)
from sqlalchemy.sql import func
from app.db.database import Base


class OHLCVCrypto(Base):
    __tablename__ = "ohlcv_crypto"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(12), nullable=False, index=True)
    ts = Column(DateTime(timezone=True), nullable=False, index=True)
    open = Column(Numeric(18, 8))
    high = Column(Numeric(18, 8))
    low = Column(Numeric(18, 8))
    close = Column(Numeric(18, 8))
    volume = Column(Numeric(24, 8))
    vwap = Column(Numeric(18, 8))
    __table_args__ = (
        UniqueConstraint('symbol', 'ts', name='uix_crypto_symbol_ts'),
        {"extend_existing": True},               # ← fixes "already defined" on re-import
    )


class OHLCVStocks(Base):
    __tablename__ = "ohlcv_stocks"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    ts = Column(Date, nullable=False, index=True)
    open = Column(Numeric(12, 2))
    high = Column(Numeric(12, 2))
    low = Column(Numeric(12, 2))
    close = Column(Numeric(12, 2))
    volume = Column(BigInteger)
    __table_args__ = (
        UniqueConstraint('symbol', 'ts', name='uix_stock_symbol_ts'),
        {"extend_existing": True},
    )


class FinancialReports(Base):
    __tablename__ = "financial_reports"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    period = Column(String(8), nullable=False)
    report_type = Column(String(20), nullable=False)
    data = Column(JSON, nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint('symbol', 'period', 'report_type', name='uix_financial_report'),
        {"extend_existing": True},
    )


class Watchlist(Base):
    __tablename__ = "watchlist"
    symbol = Column(String(10), primary_key=True)
    asset_type = Column(String(10), nullable=False)
    active = Column(Boolean, default=True)
    __table_args__ = ({"extend_existing": True},)


class ModelRegistry(Base):
    __tablename__ = "model_registry"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(12), nullable=False, index=True)
    model_type = Column(String(10), nullable=False)
    version = Column(Integer, nullable=False)
    metrics = Column(JSON)
    artifact_path = Column(String(500))
    trained_at = Column(DateTime(timezone=True), server_default=func.now())
    active = Column(Boolean, default=False)
    __table_args__ = ({"extend_existing": True},)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(16), nullable=False, default="user")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = ({"extend_existing": True},)


class RequestLog(Base):
    __tablename__ = "request_logs"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    method = Column(String(10), nullable=False)
    path = Column(String(512), nullable=False)
    status_code = Column(Integer, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    client_ip = Column(String(64), nullable=False)
    username = Column(String(64), nullable=True)
    logged_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        Index("idx_rl_logged_at", "logged_at"),  # ← proper Index objects
        Index("idx_rl_path", "path"),             #   replaces invalid postgresql_indexes dict
        Index("idx_rl_client_ip", "client_ip"),
        Index("idx_rl_username", "username"),
        {"extend_existing": True},
    )