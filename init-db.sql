-- Initialize PostgreSQL permissions for FYP
-- This script runs automatically when PostgreSQL starts

-- Create or update fyp_user with the correct password
DO $$
BEGIN
    CREATE USER fyp_user WITH PASSWORD 'fyp_secure_password_2024';
EXCEPTION WHEN duplicate_object THEN
    ALTER USER fyp_user WITH PASSWORD 'fyp_secure_password_2024';
END
$$;

-- Grant privileges to the fyp_user on the existing fyp_db database
GRANT ALL PRIVILEGES ON DATABASE fyp_db TO fyp_user;

-- Connect to the database and set schema privileges
\c fyp_db;
GRANT ALL ON SCHEMA public TO fyp_user;
ALTER SCHEMA public OWNER TO fyp_user;
