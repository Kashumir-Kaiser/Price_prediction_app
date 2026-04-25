"""Admin user seeding -- runs once at startup to ensure an admin account exists."""
import asyncio
import structlog

from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.db.models import User
from app.services.auth_service import hash_password
from app.config import get_settings

logger = structlog.get_logger()


async def seed_admin_user() -> None:
    """
    Create the admin user from environment variables if it does not already exist.

    Behaviour:
    - Reads ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD from .env / environment.
    - Idempotent: if a user with ADMIN_USERNAME already exists, this function does nothing
      (it does NOT update the password -- change via /api/admin/users or delete + re-seed).
    - Called once from entrypoint.sh before uvicorn starts.

    Security:
    - ADMIN_PASSWORD is hashed with bcrypt before storage.
    - The plaintext value is never written to disk or logged.
    - ADMIN_PASSWORD env var should be unset or rotated after first deployment.
    """
    settings = get_settings()

    # Validate required field at runtime -- fail loudly if missing
    if not settings.admin_password:
        raise RuntimeError(
            "[seed_admin] ADMIN_PASSWORD environment variable is not set. "
            "Add it to your .env file and restart."
        )

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.username == settings.admin_username)
        )
        existing = result.scalars().first()

        if existing:
            logger.info(
                "[seed_admin] Admin '%s' already exists -- skipping.",
                settings.admin_username,
            )
            return

        admin = User(
            username=settings.admin_username,
            email=settings.admin_email,
            password_hash=hash_password(settings.admin_password),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        await db.commit()

        # Log username only -- NEVER log the plaintext password
        logger.info(
            "[seed_admin] Admin user '%s' created successfully.",
            settings.admin_username,
        )


if __name__ == "__main__":
    asyncio.run(seed_admin_user())
