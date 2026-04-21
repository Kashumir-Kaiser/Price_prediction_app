#!/usr/bin/env bash
set -e

# Run database migrations (if alembic is configured)
# cd /app && alembic upgrade head || echo "No migrations to run"

# Start application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000