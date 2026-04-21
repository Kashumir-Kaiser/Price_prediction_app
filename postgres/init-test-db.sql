-- postgres/init-test-db.sql
-- Runs once when the postgres container is first created (fresh volume).
-- Executed as POSTGRES_USER (see postgres docker-entrypoint). Creates the
-- test DB owned by that user so the healthcheck and pytest can connect.

SELECT format(
    'CREATE DATABASE market_db_test OWNER %I',
    session_user::text
)
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'market_db_test'
)\gexec

-- Redundant for owner, but keeps behavior explicit if ownership ever differs.
GRANT ALL PRIVILEGES ON DATABASE market_db_test TO CURRENT_USER;