-- Run once as a PostgreSQL administrator.
-- Change the password before production use.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hospital360_ai') THEN
        CREATE ROLE hospital360_ai LOGIN PASSWORD 'CHANGE_ME_STRONG_PASSWORD';
    END IF;
END
$$;

ALTER ROLE hospital360_ai SET default_transaction_read_only = on;
ALTER ROLE hospital360_ai SET statement_timeout = '15s';
ALTER ROLE hospital360_ai SET idle_in_transaction_session_timeout = '15s';

GRANT CONNECT ON DATABASE hospital360 TO hospital360_ai;
GRANT USAGE ON SCHEMA analytics, warehouse TO hospital360_ai;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics, warehouse TO hospital360_ai;

ALTER DEFAULT PRIVILEGES IN SCHEMA analytics
GRANT SELECT ON TABLES TO hospital360_ai;

ALTER DEFAULT PRIVILEGES IN SCHEMA warehouse
GRANT SELECT ON TABLES TO hospital360_ai;

REVOKE CREATE ON SCHEMA public FROM hospital360_ai;
