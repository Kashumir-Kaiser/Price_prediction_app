"""Pydantic settings configuration for the backend."""
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(
        # Singular form 'protected_namespace' is silently ignored,
        protected_namespaces=(),
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    # Alpaca Markets API
    alpaca_api_key: str = Field(default="", alias="ALPACA_API_KEY")
    alpaca_secret_key: str = Field(default="", alias="ALPACA_SECRET_KEY")

    # PostgreSQL
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="market_db", alias="POSTGRES_DB")
    postgres_user: str = Field(default="market_user", alias="POSTGRES_USER")
    postgres_password: str = Field(default="", alias="POSTGRES_PASSWORD")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Application
    api_key: str = Field(default="internal_x_api_key", alias="API_KEY")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # ML / Model Cache
    model_cache_dir: str = Field(default="/model-cache", alias="MODEL_CACHE_DIR")
    model_base_url: Optional[str] = Field(default=None, alias="MODEL_BASE_URL")

    # Rate Limiting
    alpaca_rate_limit_rpm: int = Field(default=200, alias="ALPACA_RATE_LIMIT_RPM")
    vnstock_sleep_between_tickers: int = Field(default=2, alias="VNSTOCK_SLEEP_BETWEEN_TICKERS")

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="CHANGE_ME_IN_PRODUCTION_USE_32_CHAR_MIN", alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60, alias="JWT_EXPIRE_MINUTES")
    bcrypt_rounds: int = Field(default=12, alias="BCRYPT_ROUNDS")

    @property
    def database_url(self) -> str:
        """Construct async PostgreSQL URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        """Construct sync PostgreSQL URL for migrations."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()