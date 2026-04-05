-- postgres/init-test-db.sql
-- Runs once when the postgres container is first created (fresh volume).
-- Creates the test database owned by the same application user.
-- The main database (market_db) is already created by the POSTGRES_DB env var.

\set test_db_name 'market_db_test'

SELECT 'CREATE DATABASE market_db_test OWNER ' || current_user
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'market_db_test'
)\gexec

-- Grant all privileges to the app user so tests can create/drop schemas freely.
GRANT ALL PRIVILEGES ON DATABASE market_db_test TO current_user;