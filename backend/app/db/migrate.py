"""Database migration script."""
import asyncio
from sqlalchemy import create_engine
from app.db.database import Base
from app.config import get_settings
settings = get_settings()


def run_migrations():
    """Run database migrations synchronously."""
    engine = create_engine(settings.sync_database_url)
    Base.metadata.create_all(bind=engine)
    print("Database migrations completed successfully")


if __name__ == "__main__":
    run_migrations()
