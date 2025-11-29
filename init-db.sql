-- Initialize PostgreSQL permissions for FYP
-- This script runs automatically when PostgreSQL starts

-- Grant privileges to the fyp_user on the existing fyp_db database
GRANT ALL PRIVILEGES ON DATABASE fyp_db TO fyp_user;

-- Connect to the database and set schema privileges
\c fyp_db;
GRANT ALL ON SCHEMA public TO fyp_user;
ALTER SCHEMA public OWNER TO fyp_user;
