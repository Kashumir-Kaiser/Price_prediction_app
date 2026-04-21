#!/bin/bash
set -e

echo "[entrypoint] Waiting for PostgreSQL..."
until pg_isready -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -q; do
    sleep 1
done

echo "[entrypoint] Running DB migrations..."
python -m app.db.migrate

echo "[entrypoint] Seeding admin user..."
python -m app.core.seed_admin

# If a command is provided, run it instead of starting uvicorn
if [ $# -gt 0 ]; then
    echo "[entrypoint] Executing custom command: $*"
    exec "$@"
fi

echo "[entrypoint] Checking model cache..."
# Pull pre-trained base models from remote storage if not present.
# This runs BEFORE the service starts so the API is never cold on first request.
# Set MODEL_BASE_URL in .env pointing to an S3/GCS bucket or internal model store.
if [ -n "$MODEL_BASE_URL" ]; then
    python -m app.ml.model_registry pull_all --cache-dir "$MODEL_CACHE_DIR"
else
    echo "[entrypoint] MODEL_BASE_URL not set — models will lazy-load on first prediction request."
fi

echo "[entrypoint] Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
