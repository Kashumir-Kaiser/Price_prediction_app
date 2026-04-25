#!/usr/bin/env bash
set -euo pipefail

# Exit with clear message if ADMIN_PASSWORD is not set.
# NOTE: Changing ADMIN_PASSWORD in .env does NOT update an existing admin
# password (seeding is idempotent). To force re-seed:
#   docker compose exec db psql -U market_user -d market_db -c \
#     "DELETE FROM users WHERE username='admin';"
# then restart the backend container.
if [ -z "${ADMIN_PASSWORD:-}" ]; then
  echo "[entrypoint] ERROR: ADMIN_PASSWORD env var is required."
  echo "[entrypoint] Add ADMIN_PASSWORD to your .env file and restart."
  exit 1
fi

echo "[entrypoint] Running Alembic migrations..."
alembic upgrade head

echo "[entrypoint] Seeding admin user..."
python -m app.core.seed_admin

echo "[entrypoint] Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --reload
