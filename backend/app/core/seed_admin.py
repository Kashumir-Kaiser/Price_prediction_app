"""Admin user seeding — runs once at startup to ensure an admin account exists."""
import structlog

from app.db.database import AsyncSessionLocal
from app.db.models import User
from app.services.auth_service import hash_password
from sqlalchemy import select

logger = structlog.get_logger()

ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@localhost"
ADMIN_PASSWORD = "Admin@StockApp2025!"


async def seed_admin_user() -> None:
    """
    Idempotently create the built-in admin account.

    Does nothing if a user with username 'admin' already exists.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.username == ADMIN_USERNAME)
        )
        existing = result.scalars().first()

        if existing:
            logger.info("Admin user already exists — skipping seed")
            return

        admin = User(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        await db.commit()

        logger.info("Admin user created", username=ADMIN_USERNAME)