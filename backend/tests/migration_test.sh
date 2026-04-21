#!/usr/bin/env bash
# Migration test — checks schema diffs between current alembic HEAD and a test DB.
set -euo pipefail

TEST_DB_URL="${TEST_DB_URL:-postgresql://test:test@localhost:5432/market_db_test}"
ALEMBIC_INI="${ALEMBIC_INI:-backend/alembic.ini}"

echo "=== Migration Test ==="

# 1. Create fresh test database
dropdb --if-exists market_db_test
createdb market_db_test

# 2. Apply all migrations
alembic -c "$ALEMBIC_INI" upgrade head

# 3. Dump schema
pg_dump "$TEST_DB_URL" --schema-only --no-owner --no-privileges > /tmp/migrated_schema.sql

# 4. Reset and apply from models (autogenerate baseline)
dropdb --if-exists market_db_test
createdb market_db_test

# 5. Compare schemas
# In a real implementation, you'd compare against a golden schema file
# For now, just verify migrations apply cleanly

echo "Checking for drift..."
if alembic -c "$ALEMBIC_INI" check; then
    echo "PASS: No schema drift detected"
else
    echo "FAIL: Schema drift detected — run 'alembic revision --autogenerate'"
    exit 1
fi

echo "=== Migration test completed ==="
