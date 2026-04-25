"""Database migration script using Alembic."""
import os
from alembic.config import Config
from alembic import command


def run_migrations() -> None:
    """Run Alembic upgrade head -- idempotent, versioned, reversible."""
    cfg = Config(os.path.join(os.path.dirname(__file__), "../../alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", _get_sync_url())
    command.upgrade(cfg, "head")
    print("[migrate] Alembic upgrade head completed.")


def _get_sync_url() -> str:
    from app.config import get_settings
    return get_settings().sync_database_url


if __name__ == "__main__":
    run_migrations()
