-- ============================================
-- PostgreSQL initialization script
-- Executed on first container start
-- ============================================

-- Create btree_gist extension for EXCLUDE constraints
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Create uuid-ossp extension for UUID generation (if needed)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant privileges (adjust as needed)
-- Note: The main database and user are created by Docker environment variables
-- This script runs additional initialization

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialized with btree_gist extension for booking overlap prevention';
END $$;
